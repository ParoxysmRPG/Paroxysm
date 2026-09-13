#!/usr/bin/env python3
"""Repair reviewed sky traps and unnamed town rooms. Dry run unless --write."""
import argparse
import json
import re

from audit_world_map import ROOT
from audit_institute import EXIT
from describe_world import records, plain


def repair(write=False):
    path = ROOT / 'area/hvntown.are'
    raw = path.read_bytes()
    text = raw.decode().replace('\r\n', '\n')
    prefix, section = text.split('#ROOMS\n', 1)
    changes = []
    names = {2: '`wAn Unfinished Room`x', 9: '`wAn Unfinished Commercial Room`x',
             10: '`gAn Open Plot`x', 13: '`wAn Exposed Rooftop`x'}
    # The sky above two roof surfaces must permit return to those same roofs.
    # The lawn below 5210 has no stair opening through the roof.
    walls = {(9313, 5): 0, (3879, 5): 0, (5210, 5): 4, (6868, 5): 4,
             (3021, 5): 0, (3311, 5): 0, (3304, 5): 0,
             (3179, 5): 0, (3386, 5): 0, (3382, 5): 0}
    for m in reversed(records(text)):
        n = int(m[1]); body = m[5]; name = m[2]
        if not plain(name):
            name = names[int(m[4].split()[2])]
        def fix(e):
            target = walls.get((n, int(e[1])))
            state = list(map(int, e[7].split()))
            if target is None or state[3] == target:
                return e[0]
            state[3] = target
            return f'D{e[1]}\n{e[2]}~\n{e[3]}~\n{e[4]} {e[5]} {e[6]}\n' + ' '.join(map(str, state)) + '\n'
        body = EXIT.sub(fix, body)
        if body == m[5] and name == m[2]:
            continue
        replacement = f'#{n}\n{name}~\n{m[3]}~\n{m[4]}\n{body}'
        section = section[:m.start()] + replacement + section[m.end():]
        changes.append({'vnum': n, 'before_name': plain(m[2]), 'name': plain(name),
                        'exit_change': body != m[5]})
    result = prefix + '#ROOMS\n' + section
    records(result)
    print(f'{len(changes)} reviewed egress/name changes.')
    if write and changes:
        path.write_bytes(result.replace('\n', '\r\n').encode() if b'\r\n' in raw else result.encode())
        report = ROOT / 'docs/map-egress-repairs.json'
        previous = json.loads(report.read_text()) if report.exists() else []
        report.write_text(json.dumps(previous + changes, indent=2) + '\n', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    repair(parser.parse_args().write)
