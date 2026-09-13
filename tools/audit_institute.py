#!/usr/bin/env python3
"""Check institute terrain, assigned rooms, doors and structural boundaries."""
import argparse
import collections
import json
from pathlib import Path
import re

from describe_world import records, plain

ROOT = Path(__file__).resolve().parents[1]
EXIT = re.compile(r'^D(\d+)\n([^~]*)~\n([^~]*)~\n(\d+) (-?\d+) (\d+)\n([^\n]+)\n', re.M)
REVERSE = [2, 3, 0, 1, 5, 4, 9, 8, 7, 6]
DOORS = {1, 2, 3, 4, 6, 7, 8, 9}
HOUSE_NAMES = {'REP': 'Repentance', 'PUR': 'Purity', 'FOR': 'Forbearance', 'CHAR': 'Charity'}


def roof_name(name):
    return bool(re.search(r'rooftop|atop a covered walkway|top of the biodome airlock', name, re.I))


def read_rooms():
    result = {}
    for m in records((ROOT / 'area/hvntown.are').read_text()):
        result[int(m[1])] = {
            'name': plain(m[2]), 'flags': int(m[4].split()[1]),
            'sector': int(m[4].split()[2]), 'description': m[3],
            'coords': tuple(map(int, re.search(r'^C (.*)', m[5], re.M)[1].split())),
            'exits': {int(e[1]): {'kind': int(e[4]), 'to': int(e[6]),
                                 'state': list(map(int, e[7].split()))}
                      for e in EXIT.finditer(m[5])}
        }
    return result


def in_scope(room):
    x, y, _ = room['coords']
    return 1 <= x <= 23 and 48 <= y <= 71


def assigned_rooms():
    names = ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX']
    return {int(vnum): f'{HOUSE_NAMES[house]} {names.index(number) + 1}'
            for house, number, vnum in re.findall(
                r'#define COLLEGE_ROOM_(REP|PUR|FOR|CHAR)_(\w+) (\d+)',
                (ROOT / 'src/const.h').read_text())}


def world_room_ids():
    """Cross-area exits are valid when their destination is in another loaded area."""
    result = set()
    for filename in (ROOT / 'area/area.lst').read_text().split():
        path = ROOT / 'area' / filename
        if not path.is_file():
            continue
        text = path.read_text()
        if '#ROOMS\n' in text:
            section = text.split('#ROOMS\n', 1)[1].split('#RESETS', 1)[0]
            result.update(int(n) for n in re.findall(r'^#(\d+)$', section, re.M))
    return result


def audit(rooms):
    findings = []
    existing = world_room_ids()
    def issue(kind, vnum, **details):
        findings.append({'kind': kind, 'vnum': vnum, **details})
    for n, room in rooms.items():
        if not in_scope(room):
            continue
        name, flags, sector = room['name'], room['flags'], room['sector']
        if roof_name(name) and (sector != 13 or flags & (8 | 8192)):
            issue('roof_terrain_or_flags', n)
        # The enclosed air above the biodome canopy intentionally has no floor.
        dome_air = 'biodome' in name.lower() and room['coords'][2] > 0 and not flags & 8192
        if sector == 18 and flags & (8 | 8192) and not dome_air:
            issue('air_with_indoor_or_bedroom_flags', n)
        if re.fullmatch(r'(?:a )?grassy field', name, re.I) and sector in {20, 21, 28}:
            issue('flooded_field', n)
        if re.search(r'\boffice$', name, re.I) and sector in {10, 18, 20, 21, 23, 28}:
            issue('office_terrain', n)
        if sector == 29 and re.search(r'corridor', name, re.I) and not flags & 8:
            issue('outdoor_indoor_corridor', n)
        if re.search(r'\bgarden\b', name, re.I) and flags & 8192:
            issue('garden_bedroom_flag', n)
        if flags & 8 and sector in {2, 3, 4, 5, 6, 8, 9, 12, 14, 15, 29}:
            if not any(e['state'][3] == 0 for e in room['exits'].values()):
                issue('sealed_interior', n)
        for d, e in room['exits'].items():
            to = rooms.get(e['to'])
            if not to:
                if e['to'] not in existing:
                    issue('missing_exit_destination', n, direction=d, to=e['to'])
                continue
            if not in_scope(to):
                continue
            back = to['exits'].get(REVERSE[d])
            ordinary = e['state'][3] == 0 and not any(e['state'][:3])
            structure = flags & 8 or to['flags'] & 8 or roof_name(name) or roof_name(to['name'])
            if ordinary and structure and (not back or back['to'] != n or back['state'][3] != 0):
                issue('one_way_structural_boundary', n, direction=d, to=e['to'])
            if ordinary and e['kind'] in DOORS and back and back['to'] == n:
                if back['state'][3] == 0 and back['kind'] not in DOORS:
                    issue('one_sided_door', n, direction=d, to=e['to'])
    for n, name in assigned_rooms().items():
        if n not in rooms:
            issue('missing_assigned_bedroom', n)
        elif rooms[n]['name'] != name or rooms[n]['sector'] != 2 or not rooms[n]['flags'] & 8192:
            issue('assigned_bedroom_identity', n, expected=name)
    for n, floor in [(3347, 1), (16156, 0)]:
        room = rooms[n]
        if room['sector'] != 2 or not room['flags'] & 8 or room['coords'] != (5, 60, floor):
            issue('nexus_floor', n)
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rooms = read_rooms()
    findings = audit(rooms)
    result = {'rooms_checked': sum(in_scope(r) for r in rooms.values()),
              'finding_counts': dict(collections.Counter(f['kind'] for f in findings)),
              'findings': findings}
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'findings'}, indent=2))
    raise SystemExit(bool(findings))


if __name__ == '__main__':
    main()
