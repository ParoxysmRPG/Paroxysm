#!/usr/bin/env python3
"""Read-only audit of loaded area rooms; findings are candidates, not all bugs."""
import argparse
import collections
import json
from pathlib import Path
import re

from audit_institute import DOORS, EXIT, REVERSE
from describe_world import plain, records

ROOT = Path(__file__).resolve().parents[1]
GRID_AREAS = {'hvntown.are', 'hvnocean.are', 'nforest.are', 'sforest.are', 'wforest.are',
              'onforest.are', 'osforest.are', 'owforest.are', 'otherfor.are',
              'wildfor.are', 'godfor.are', 'hellfor.are'}
DELTAS = [(0, 1, 0), (1, 0, 0), (0, -1, 0), (-1, 0, 0), (0, 0, 1),
          (0, 0, -1), (1, 1, 0), (-1, 1, 0), (1, -1, 0), (-1, -1, 0)]
SKY_NAME = re.compile(r'(?:a |the )?(?:sky|skies|air)', re.I)


def read_world():
    rooms = {}
    for filename in (ROOT / 'area/area.lst').read_text().split():
        path = ROOT / 'area' / filename
        if not path.is_file():
            continue
        for m in records(path.read_text()):
            n = int(m[1])
            exits = list(EXIT.finditer(m[5]))
            directions = [int(e[1]) for e in exits]
            if len(exits) != len(re.findall(r'^D\d+$', m[5], re.M)):
                raise ValueError(f'Unparsed exit in {filename} room {n}')
            if len(directions) != len(set(directions)) or any(d not in range(10) for d in directions):
                raise ValueError(f'Invalid or repeated exit direction in room {n}')
            for e in exits:
                state = list(map(int, e[7].split()))
                if int(e[4]) not in range(12) or len(state) != 9 or state[3] not in range(6):
                    raise ValueError(f'Invalid exit record in room {n}, direction {e[1]}')
            copies = rooms.get(n, {}).get('copies', 0) + 1
            rooms[n] = {
                'area': filename, 'name': plain(m[2]), 'copies': copies, 'flags': int(m[4].split()[1]),
                'sector': int(m[4].split()[2]),
                'coords': tuple(map(int, re.search(r'^C (.*)', m[5], re.M)[1].split())),
                'exits': {int(e[1]): {'kind': int(e[4]), 'key': int(e[5]), 'to': int(e[6]),
                                     'state': list(map(int, e[7].split()))}
                          for e in exits}}
    return rooms


def roof(name):
    return bool(re.search(r'rooftop|atop a covered walkway|top of the biodome airlock', name, re.I)
                or re.fullmatch(r'(?:a |the )?roof', name, re.I))


def campus(room):
    x, y, _ = room['coords']
    return room['area'] == 'hvntown.are' and 1 <= x <= 23 and 48 <= y <= 71


def market_slots():
    """All configured market slots, including currently inactive brick walls."""
    directions = {}
    for record in (ROOT / 'data/properties.txt').read_text().split('#PROPERTY')[1:]:
        n = re.search(r'^MarketRoom (\d+)', record, re.M)
        d = re.search(r'^MarketDir (\d+)', record, re.M)
        if n and d and int(n[1]):
            directions[int(n[1])] = int(d[1])
    return directions


def market_routes(rooms):
    """Market return directions come from property data, not compass opposites."""
    directions = market_slots()
    return [(n, d, e['to'], directions[e['to']])
            for n in range(405000, 405004) for d, e in rooms[n]['exits'].items()
            if d in {1, 3} and e['to'] in directions]


def physical_findings(rooms):
    """Evidence from coordinates and terrain, independent of ordinary door symmetry."""
    findings = []
    coords = collections.defaultdict(list)
    area_coords = collections.defaultdict(list)
    for n, r in rooms.items():
        if r['area'] in GRID_AREAS:
            coords[r['coords']].append(n)
            area_coords[r['area'], r['coords']].append(n)
    slots = set(market_slots().items())
    for n, r in rooms.items():
        def issue(kind, **details):
            findings.append({'kind': kind, 'vnum': n, 'area': r['area'], 'name': r['name'], **details})
        if r['sector'] == 13 and SKY_NAME.fullmatch(r['name']):
            issue('roof_named_sky')
        if r['sector'] in {2, 9} and SKY_NAME.fullmatch(r['name']):
            issue('solid_floor_named_sky')
        if r['area'] == 'hvntown.are' and not r['name']:
            issue('unnamed_town_room')
        if r['area'] == 'hvntown.are' and r['sector'] == 24 and r['coords'][2] < 0:
            surface = area_coords[r['area'], (*r['coords'][:2], 0)]
            for a in surface:
                t = rooms[a]
                if t['name'] == r['name'] and t['sector'] in {1, 7, 10, 23, 26, 27, 29, 30, 31, 32}:
                    issue('cave_named_after_surface', surface=a)
                    break
        if r['area'] not in GRID_AREAS:
            continue
        for d, e in r['exits'].items():
            if d >= len(DELTAS) or (n, d) in slots or e['kind'] != 0 or e['state'][3] != 0:
                continue
            t = rooms.get(e['to'])
            if not t or t['area'] not in GRID_AREAS:
                continue
            wanted = tuple(a + b for a, b in zip(r['coords'], DELTAS[d]))
            if t['coords'] == wanted:
                continue
            choices = coords[wanted]
            if len(choices) != 1:
                continue
            back = rooms[choices[0]]['exits'].get(REVERSE[d])
            if back and back['to'] == n and back['state'][3] == 0:
                issue('wrong_adjacent_destination', direction=d, to=e['to'], expected=choices[0])
    for position, ids in coords.items():
        if len(ids) > 1 and position != (0, 0, 0):
            area = rooms[min(ids)]['area']
            findings.append({'kind': 'duplicate_coordinates', 'vnum': min(ids), 'area': area,
                             'name': rooms[min(ids)]['name'], 'coords': position, 'rooms': ids})
    return findings


def town_egress(rooms):
    """Check graph egress, allowing doors and traversal skills but respecting walls."""
    outgoing = collections.defaultdict(list)
    incoming = collections.defaultdict(list)
    for n, r in rooms.items():
        for e in r['exits'].values():
            if e['state'][3] == 0 or e['state'][4] == 2:
                outgoing[n].append(e['to'])
                incoming[e['to']].append(n)
    def reachable(graph):
        seen = {2617}
        pending = [2617]
        while pending:
            for n in graph[pending.pop()]:
                if n not in seen:
                    seen.add(n)
                    pending.append(n)
        return seen
    entered = reachable(outgoing)
    return {'reachable_from_town': len(entered),
            'without_return': sorted(entered - reachable(incoming))}


def check_door_resets(rooms):
    findings = []
    for area in {r['area'] for r in rooms.values()}:
        text = (ROOT / 'area' / area).read_text()
        for block in re.findall(r'^#RESETS\n(.*?)(?=^#)', text, re.M | re.S):
            for n, d, state in re.findall(r'^D\s+0\s+(\d+)\s+(\d+)\s+(\d+)', block, re.M):
                n, d, state = int(n), int(d), int(state)
                if n not in rooms or d not in rooms[n]['exits'] or state not in {0, 1, 2}:
                    findings.append({'kind': 'invalid_door_reset', 'area': area,
                                     'vnum': n, 'direction': d, 'state': state})
    return findings


def audit(rooms):
    findings = physical_findings(rooms) + check_door_resets(rooms)
    for n in town_egress(rooms)['without_return']:
        r = rooms[n]
        # The old well has an explicit falling entrance and confinement flags.
        # Keep it visible as a hazard review, not an automatically added ladder.
        kind = 'hazard_egress_review' if n == 2044 else 'no_return_to_town'
        findings.append({'kind': kind, 'vnum': n, 'area': r['area'], 'name': r['name']})
    portals = market_routes(rooms)
    special_edges = {(n, d) for n in range(405000, 405004) for d in (1, 3)}
    special_edges.update(market_slots().items())
    for a, d, b, back in portals:
        e = rooms[b]['exits'].get(back)
        if not e or e['to'] != a or e['state'][3] != 0:
            findings.append({'kind': 'market_connection_review', 'vnum': b, 'area': rooms[b]['area'],
                             'name': rooms[b]['name'], 'direction': back, 'to': a,
                             'note': 'Runtime-managed market slot; do not repair as a local doorway.'})
    for n, r in rooms.items():
        if campus(r):
            continue
        def issue(kind, **details):
            findings.append({'kind': kind, 'vnum': n, 'area': r['area'], 'name': r['name'],
                             'sector': r['sector'], **details})
        if r['copies'] > 1:
            issue('duplicate_room', copies=r['copies'])
        if roof(r['name']) and (r['sector'] != 13 or r['flags'] & (8 | 8192)):
            issue('roof_terrain_or_flags')
        if r['flags'] & 8 and r['sector'] in {2, 3, 4, 5, 6, 8, 9, 12, 14, 15, 29}:
            if not any(e['state'][3] == 0 or e['state'][4] == 2 for e in r['exits'].values()):
                issue('sealed_interior', exit_count=len(r['exits']))
        for d, e in r['exits'].items():
            t = rooms.get(e['to'])
            if not t:
                issue('missing_exit_destination', direction=d, to=e['to'])
                continue
            if (n, d) in special_edges:
                continue
            b = t['exits'].get(REVERSE[d])
            ordinary = e['state'][3] == 0 and not any(e['state'][:3])
            structure = r['flags'] & 8 or t['flags'] & 8 or roof(r['name']) or roof(t['name'])
            if ordinary and structure and (not b or b['to'] != n or b['state'][3] != 0):
                issue('one_way_structural_boundary', direction=d, to=e['to'], to_name=t['name'])
            if ordinary and e['kind'] in DOORS and b and b['to'] == n:
                if b['state'][3] == 0 and b['kind'] not in DOORS:
                    issue('one_sided_door', direction=d, to=e['to'], to_name=t['name'],
                          note='Unclassified: may be a market door; symmetry alone is not evidence of a bug.')
    return findings


def report(rooms, findings):
    physical_kinds = {'roof_named_sky', 'solid_floor_named_sky', 'cave_named_after_surface',
                      'unnamed_town_room', 'wrong_adjacent_destination', 'duplicate_coordinates',
                      'duplicate_room', 'missing_exit_destination', 'invalid_door_reset', 'no_return_to_town'}
    return {'rooms_loaded': len(rooms), 'institute_rooms_excluded': sum(map(campus, rooms.values())),
            'confirmed_check_findings': sum(f['kind'] in physical_kinds for f in findings),
            'egress': town_egress(rooms),
            'candidate_counts': dict(collections.Counter(f['kind'] for f in findings)),
            'candidate_rooms': len({f['vnum'] for f in findings}),
            'area_counts': dict(collections.Counter(f['area'] for f in findings)), 'findings': findings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rooms = read_world()
    result = report(rooms, audit(rooms))
    if args.report:
        args.report.write_text(json.dumps(result, indent=2) + '\n', newline='\n')
    print(json.dumps({k: v for k, v in result.items() if k not in {'findings', 'area_counts'}}, indent=2))
