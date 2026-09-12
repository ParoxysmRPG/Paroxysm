"""Durable, single-worker CSV request consumption and JSON Lines results.

Requests stay in the append-only input file. A separate cursor advances only
after success (or durable quarantine), so a stopped worker retries its job.
"""
import csv
import fcntl
import json
import logging
import os
import shutil
from pathlib import Path
import tempfile
from contextlib import contextmanager

csv.field_size_limit(16 * 1024 * 1024)


@contextmanager
def locked(path, nonblocking=False):
    with open(str(path) + '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | (fcntl.LOCK_NB if nonblocking else 0))
        yield


def atomic_json(path, value):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.tmp.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def append_json(path, value):
    record = (json.dumps(value, ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')
    with locked(path):
        # Unbuffered writes let us roll back a failed partial append before
        # releasing the lock, keeping the next retry on a clean record boundary.
        with open(path, 'a+b', buffering=0) as stream:
            start = stream.tell()
            try:
                remaining = memoryview(record)
                while remaining:
                    count = stream.write(remaining)
                    if not count:
                        raise OSError('Unable to append AI record')
                    remaining = remaining[count:]
                os.fsync(stream.fileno())
            except BaseException:
                stream.truncate(start)
                os.fsync(stream.fileno())
                raise
        parent = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)


def append_result(path, fields):
    # Strings keep numeric IDs and the legacy engine field layout unchanged.
    if any(value is None for value in fields):
        raise ValueError('AI response is missing a required field')
    values = [str(value) for value in fields]
    if any('\0' in value or '~' in value or len(value.encode('utf-8')) > 16000 for value in values):
        raise ValueError('AI response contains an unsupported or oversized field')
    def integer(index, low, high):
        value = values[index]
        return value.isascii() and value.isdecimal() and low <= int(value) <= high
    def name(index):
        value = values[index]
        return 0 < len(value) <= 64 and value.isascii() and value.isalpha()
    if not values or not integer(0, 1, 6):
        raise ValueError('Invalid AI response type')
    kind = int(values[0])
    if len(values) != [0, 3, 6, 4, 6, 4, 11][kind] and not (kind == 2 and len(values) == 9):
        raise ValueError('Invalid AI response field count')
    valid = {
        1: lambda: integer(1, 1, 2147483647) and bool(values[2]),
        2: lambda: all(values[i] for i in (1, 2, 3, 4)) and len(values[5].encode('utf-8')) >= 10 and
           (len(values) == 6 or (integer(6, 0, 2147483647) and integer(7, 1, 2147483647) and integer(8, 0, 2147483647))),
        3: lambda: name(1) and integer(2, 0, 36500) and bool(values[3]),
        4: lambda: name(1) and name(3) and integer(2, 0, 100) and integer(4, 0, 100),
        5: lambda: bool(values[1]) and bool(values[3]),
        6: lambda: name(1) and name(2) and all(values[i] for i in (3, 4, 5)) and integer(8, 1, 10) and integer(9, 0, 11),
    }[kind]()
    if not valid:
        raise ValueError('Invalid AI response values')
    append_json(path, values)


def compact_requests(path, cursor):
    """Replace a large acknowledged prefix; the inode change resets its cursor."""
    offset = cursor.get('offset', 0)
    if offset < 1024 * 1024:
        return
    with locked(path):
        with open(path, 'rb') as source:
            info = os.fstat(source.fileno())
            if cursor.get('identity') != [info.st_dev, info.st_ino] or offset > info.st_size or offset * 2 < info.st_size:
                return
            header = source.readline()
            source.seek(offset)
            fd, temporary = tempfile.mkstemp(prefix=path.name + '.tmp.', dir=path.parent)
            try:
                with os.fdopen(fd, 'wb') as output:
                    os.fchmod(output.fileno(), info.st_mode & 0o777)
                    output.write(header)
                    shutil.copyfileobj(source, output)
                    output.flush()
                    os.fsync(output.fileno())
                # The old cursor was already committed. Both sides of a crash
                # at this rename identify the unread suffix correctly.
                os.replace(temporary, path)
                parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(parent)
                finally:
                    os.close(parent)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)


def next_record(path, quotechar, cursor):
    """Return one complete record and its identity/offset under the producer lock."""
    with locked(path):
        with open(path, 'rb') as stream:
            info = os.fstat(stream.fileno())
            identity = [info.st_dev, info.st_ino]
            if cursor.get('identity') != identity or cursor.get('offset', 0) > info.st_size:
                cursor = {'identity': identity, 'offset': 0, 'attempts': 0}
            # byte-oriented iterator keeps an exact offset even for multiline CSV.
            def lines():
                while True:
                    line = stream.readline()
                    if not line or not line.endswith(b'\n'):
                        return
                    yield line.decode('utf-8')
            reader = csv.reader(lines(), quotechar=quotechar, strict=True)
            header = next(reader, None)
            if header is None:
                return None
            if cursor['offset']:
                stream.seek(cursor['offset'])
                reader = csv.reader(lines(), quotechar=quotechar, strict=True)
            start = stream.tell()
            try:
                row = next(reader, None)
            except csv.Error:
                # A legacy producer may still be writing its final quoted field.
                if stream.tell() == info.st_size:
                    return None
                raise
            if row is None:
                return None
            state = dict(cursor, identity=identity, offset=start)
            return header, row, stream.tell(), state


def process_requests(path, handler, quotechar='"', limit=32, max_attempts=5):
    """Process a bounded batch; one worker owns each queue across API calls.

    A crash after a side effect but before acknowledgement can replay that job;
    handlers should be idempotent. Only acknowledged prefixes are compacted.
    Failed jobs are retained in <path>.failed.jsonl after bounded retries.
    """
    path = Path(path)
    cursor_path = Path(str(path) + '.worker-cursor')
    if not path.exists():
        return 0
    completed = 0
    try:
        with locked(str(path) + '.worker', nonblocking=True):
            cursor = json.loads(cursor_path.read_text()) if cursor_path.exists() else {}
            seen = set()
            for _ in range(limit):
                record = next_record(path, quotechar, cursor)
                if record is None:
                    break
                header, row, end, state = record
                try:
                    if len(row) != len(header):
                        raise ValueError('CSV request field count does not match its header')
                    if tuple(row) not in seen:
                        handler(dict(zip(header, row)))
                        seen.add(tuple(row))
                except Exception as error:
                    state['attempts'] = state.get('attempts', 0) + 1
                    logging.exception('AI request failed in %s at byte %s', path, state['offset'])
                    if state['attempts'] < max_attempts:
                        atomic_json(cursor_path, state)
                        break
                    append_json(str(path) + '.failed.jsonl', {
                        'header': header, 'row': row, 'error': str(error),
                        'identity': state['identity'], 'offset': state['offset'],
                    })
                cursor = dict(state, offset=end, attempts=0)
                atomic_json(cursor_path, cursor)
                completed += 1
            compact_requests(path, cursor)
    except BlockingIOError:
        pass  # Another worker owns this queue.
    return completed
