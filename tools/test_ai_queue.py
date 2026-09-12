#!/usr/bin/env python3
"""Exercise real queue helpers without pandas, network calls, or live files."""
import csv
import io
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import ai_queue
logging.disable(logging.CRITICAL)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='haven-ai-queue-')
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'input.csv'
        self.path.write_text('Type,ID\n1,10\n')

    def test_worker_disabled_without_optional_packages_or_queue_access(self):
        for value in (None, '', '0', 'true'):
            env = dict(os.environ)
            env.pop('HAVEN_ENABLE_AI', None)
            if value is not None:
                env['HAVEN_ENABLE_AI'] = value
            before = sorted(Path(self.temp.name).iterdir())
            result = subprocess.run([sys.executable, '-S', str(ROOT / 'src/run_ai_engine.py')],
                                    cwd=self.temp.name, env=env, capture_output=True,
                                    text=True, timeout=10, check=True)
            self.assertIn('disabled', result.stdout)
            self.assertEqual(before, sorted(Path(self.temp.name).iterdir()))

    def test_worker_dispatch_requires_opt_in_and_can_be_reenabled(self):
        import run_ai_engine as worker
        with patch.dict(os.environ, {'HAVEN_ENABLE_AI': '0'}):
            with self.assertRaises(RuntimeError):
                worker.dispatch_request({})
            with self.assertRaises(RuntimeError):
                worker.dispatch_summary({})
        with patch.dict(os.environ, {'HAVEN_ENABLE_AI': '1'}), patch.object(worker, 'create_encounter') as handler:
            worker.dispatch_request({'Type': '1', 'ID': '19'})
            handler.assert_called_once_with(19)

    def append(self, text):
        with ai_queue.locked(self.path):
            with self.path.open('a') as stream:
                stream.write(text)

    def test_arrival_during_processing_and_restart(self):
        seen = []
        def handler(row):
            seen.append(row['ID'])
            self.append('1,11\n')
        self.assertEqual(ai_queue.process_requests(self.path, handler, limit=1), 1)
        self.assertIn('1,10\n1,11\n', self.path.read_text())
        ai_queue.process_requests(self.path, lambda row: seen.append(row['ID']))
        ai_queue.process_requests(self.path, lambda row: self.fail('replayed acknowledged job'))
        self.assertEqual(seen, ['10', '11'])

    def test_crash_before_acknowledgement(self):
        code = 'import ai_queue, os; ai_queue.process_requests(' + repr(str(self.path)) + ', lambda row: os._exit(13))'
        result = subprocess.run([sys.executable, '-c', code], env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))
        self.assertEqual(result.returncode, 13)
        seen = []
        ai_queue.process_requests(self.path, seen.append)
        self.assertEqual(seen, [{'Type': '1', 'ID': '10'}])

    def test_retry_then_quarantine_and_continue(self):
        self.append('1,11\n')
        seen = []
        def handler(row):
            if row['ID'] == '10':
                raise RuntimeError('temporary failure')
            seen.append(row['ID'])
        self.assertEqual(ai_queue.process_requests(self.path, handler, max_attempts=2), 0)
        self.assertEqual(ai_queue.process_requests(self.path, handler, max_attempts=2), 2)
        failed = json.loads(Path(str(self.path) + '.failed.jsonl').read_text())
        self.assertEqual(failed['row'], ['1', '10'])
        self.assertEqual(seen, ['11'])

    def test_complete_multiline_csv_and_partial_tail(self):
        self.path.write_text('type,title,text\n1,~A~~B~,~first\nsecond~\n2,~partial~,~unfinished\n')
        seen = []
        ai_queue.process_requests(self.path, seen.append, quotechar='~')
        self.assertEqual(seen, [{'type': '1', 'title': 'A~B', 'text': 'first\nsecond'}])
        self.append('finished~\n')
        ai_queue.process_requests(self.path, seen.append, quotechar='~')
        self.assertEqual(seen[1]['text'], 'unfinished\nfinished')

    def test_busy_worker_and_bad_cursor(self):
        with ai_queue.locked(str(self.path) + '.worker'):
            self.assertEqual(ai_queue.process_requests(self.path, lambda row: self.fail()), 0)
        Path(str(self.path) + '.worker-cursor').write_text('{broken')
        with self.assertRaises(ValueError):
            ai_queue.process_requests(self.path, lambda row: self.fail())
        self.assertTrue(self.path.read_text().endswith('1,10\n'))

    def test_replacement_and_truncation(self):
        ai_queue.process_requests(self.path, lambda row: None)
        replacement = self.path.with_suffix('.new')
        replacement.write_text('Type,ID\n1,12\n')
        replacement.replace(self.path)
        seen = []
        ai_queue.process_requests(self.path, seen.append)
        self.assertEqual(seen[0]['ID'], '12')
        self.path.write_text('Type,ID\n1,1\n')
        ai_queue.process_requests(self.path, seen.append)
        self.assertEqual(seen[1]['ID'], '1')

    def test_compaction_recovers_with_old_cursor(self):
        self.path.write_text('Type,ID\n1,' + 'x' * (1024 * 1024) + '\n1,tail\n')
        ai_queue.process_requests(self.path, lambda row: None, limit=1)
        self.assertEqual(self.path.read_text(), 'Type,ID\n1,tail\n')
        seen = []
        ai_queue.process_requests(self.path, seen.append)
        self.assertEqual(seen, [{'Type': '1', 'ID': 'tail'}])

    def test_deduplicate_batch(self):
        self.append('1,10\n1,11\n')
        seen = []
        ai_queue.process_requests(self.path, seen.append)
        self.assertEqual([row['ID'] for row in seen], ['10', '11'])

    def test_failed_result_append_rolls_back(self):
        path = self.path.with_suffix('.results')
        ai_queue.append_result(path, [1, 1, 'first'])
        original = path.read_bytes()
        real_fsync = os.fsync
        calls = []
        def fail_once(fd):
            calls.append(fd)
            if len(calls) == 1:
                raise OSError('disk failure')
            return real_fsync(fd)
        with patch.object(ai_queue.os, 'fsync', side_effect=fail_once):
            with self.assertRaises(OSError):
                ai_queue.append_result(path, [1, 2, 'second'])
        self.assertEqual(path.read_bytes(), original)
        ai_queue.append_result(path, [1, 2, 'second'])
        self.assertEqual(len(path.read_text().splitlines()), 2)

    def test_result_framing_and_validation(self):
        path = self.path.with_suffix('.results')
        fields = [6, 'Alice', 'Bob', 'Smith', 'a person', 'line one\nline two ||| with "quotes"', 'black', 'blue', 6, 1, 'pale']
        ai_queue.append_result(path, fields)
        self.assertEqual(len(path.read_text().splitlines()), 1)
        self.assertEqual(json.loads(path.read_text()), list(map(str, fields)))
        for bad in ([1], [1, 10, None], [1, 10, 'bad~save'], [6, *fields[1:8], 6, 12, 'pale']):
            with self.assertRaises(ValueError):
                ai_queue.append_result(path, bad)
        self.assertEqual(len(path.read_text().splitlines()), 1)


if __name__ == '__main__':
    unittest.main()
