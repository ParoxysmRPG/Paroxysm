#!/usr/bin/env python3
"""Apply the reviewed September 2026 map repairs; dry run unless --write is set."""
import argparse
import collections
import copy
import json
import re

from audit_world_map import ROOT, audit, read_world
from audit_institute import EXIT, DOORS, REVERSE
from describe_world import records


def repair(write=False):
    rooms = read_world()
    before = copy.deepcopy(rooms)
    changes = []
    resets = {}
    for filename in {r['area'] for r in rooms.values()}:
        for n, d, state in re.findall(r'^D\s+0\s+(\d+)\s+(\d+)\s+(\d+)',
                                      (ROOT / 'area' / filename).read_text(), re.M):
            resets[int(n), int(d)] = int(state)
    reset_changes = {}

    def edit(n, d, reason, **fields):
        e = rooms[n]['exits'].setdefault(d, {'kind': 0, 'key': 0, 'to': 0, 'state': [0] * 9})
        old = copy.deepcopy(e)
        wall = fields.pop('wall', None)
        e.update(fields)
        if wall is not None:
            e['state'][3] = wall
        if old != e:
            changes.append({'room': n, 'direction': d, 'reason': reason, 'before': old, 'after': copy.deepcopy(e)})

    def door_reset(n, d, state):
        if resets.get((n, d)) != state:
            reset_changes[n, d] = state

    def pair(n, d, t, kind, reason, closed=None):
        back = REVERSE[d]
        for a, direction, b in [(n, d, t), (t, back, n)]:
            existing = rooms[a]['exits'].get(direction)
            assert existing is None or existing['to'] == b, (a, direction, b)
            edit(a, direction, reason, to=b, kind=kind, wall=0)
        if closed is not None:
            for a, direction in [(n, d), (t, back)]:
                door_reset(a, direction, closed if kind in DOORS else None)

    # Restore ordinary rooms from their own establishment, leaving market slots alone.
    for n, d, t, kind, reason in [
        (16514, 1, 16519, 1, 'Black Rose bathroom door'),
        (1836, 1, 16520, 0, 'Black Rose occult reading section'),
        (1836, 6, 16521, 1, 'Black Rose existing office door'),
        (16547, 0, 16546, 1, 'Howl at the Moon existing den door'),
        (34001, 8, 34006, 1, 'Tijuana abandoned storefront door'),
        (18438, 2, 15093, 0, 'Town Hall cafe from public lobby'),
        (16796, 2, 2527, 1, 'Petite Cuisine enclosed garden entrance'),
        (2158, 4, 7390, 0, 'Retreat stairs return from cafe'),
        (16645, 3, 16658, 1, 'Gravesend Hardware rear door'),
        (16697, 0, 16680, 6, 'Apartment 101 existing concealed office door'),
    ]:
        state = max(resets.get((n, d), 1), resets.get((t, REVERSE[d]), 1)) if kind in DOORS else None
        pair(n, d, t, kind, reason, state)

    for n in [9103, 9104, 2998, 7273, 36028, 36037]:
        rooms[n]['sector'] = 13
        rooms[n]['flags'] &= ~(8 | 8192)
    rooms[2527]['sector'] = 10
    rooms[2527]['flags'] &= ~(8 | 8192)

    # A one-sided concealed exit through a boundary between properties is not
    # evidence that the neighboring owner intended an entrance there.
    for n, d in [(14339, 1), (16680, 8), (16820, 2), (16822, 0), (1868, 2),
                 (9278, 8), (15329, 7), (16601, 0), (7283, 5), (4051, 5),
                 (405083, 3), (405083, 9), (151817, 1)]:
        edit(n, d, 'Respect existing wall on the other side of the boundary', wall=4)

    # Forest grid exits must not bypass the walls of the town's northern shops/homes.
    for f in audit(before):
        if f['kind'] != 'one_way_structural_boundary' or f['area'] != 'nforest.are':
            continue
        n, d, t = f['vnum'], f['direction'], f['to']
        if rooms[t]['area'] == 'hvntown.are':
            b = rooms[t]['exits'].get(REVERSE[d])
            if b and b['to'] == n and b['state'][3]:
                edit(n, d, 'Match town building wall at forest boundary', wall=b['state'][3])

    # Exposed roof surfaces should meet the same open air in both directions.
    for n in [2731, 2847, 2904, 2915, 2970, 2997, 3016, 3017, 3018, 3062, 3086, 3096, 3113, 3393]:
        e = rooms[n]['exits'][4]
        b = rooms[e['to']]['exits'][5]
        assert b['to'] == n and rooms[e['to']]['sector'] == 18
        edit(e['to'], 5, 'Open air over exposed rooftop', wall=0)
    # These two street-level sidewalks have no roof; fix weather and flight return.
    for n, sky in [(15031, 8278), (15057, 3796)]:
        rooms[n]['flags'] &= ~8
        pair(n, 4, sky, 0, 'Outdoor sidewalk and air above it')

    # Interior air in the dueling hall is deliberate, but its diagonal wall was one-sided.
    edit(405031, 8, 'Continuous air above the magical dueling area', wall=0)

    # Never infer ordinary doors or missing return paths from symmetry alone.
    # Goblin market doors are managed at runtime and historic property metadata
    # is incomplete, particularly outside town.
    # The later Crossroads definition is the one returned by the engine hash table.
    assert rooms[302600]['copies'] in {1, 2}
    rooms[302600]['copies'] = 1
    changed = {n for n in rooms if rooms[n] != before[n]}
    files = {rooms[n]['area'] for n in changed} | {rooms[n]['area'] for n, d in reset_changes}
    if not changed and not reset_changes:
        print('Reviewed map repairs are already applied.')
        return

    def format_exit(d, e, description='', keyword=''):
        return f'D{d}\n{description}~\n{keyword}~\n{e["kind"]} {e["key"]} {e["to"]}\n' + ' '.join(map(str, e['state'])) + '\n'

    outputs = {}
    for filename in files:
        path = ROOT / 'area' / filename
        raw = path.read_bytes()
        text = raw.decode().replace('\r\n', '\n')
        prefix, section = text.split('#ROOMS\n', 1)
        matches = records(text)
        last = {int(m[1]): m.start() for m in matches}
        for m in reversed(matches):
            n = int(m[1])
            if n == 302600 and m.start() != last[n]:
                section = section[:m.start()] + section[m.end():]
                continue
            if n not in changed:
                continue
            r = rooms[n]
            body = m[5]
            old_dirs = set()
            def replace_exit(e):
                d = int(e[1]); old_dirs.add(d)
                if before[n]['exits'].get(d) == r['exits'][d]:
                    return e[0]
                return format_exit(d, r['exits'][d], e[2], e[3])
            body = EXIT.sub(replace_exit, body)
            added = ''.join(format_exit(d, e) for d, e in sorted(r['exits'].items()) if d not in old_dirs)
            if added:
                body = re.sub(r'^S$', lambda _: added + 'S', body, flags=re.M)
            header = m[4].split(); header[1:] = [str(r['flags']), str(r['sector'])]
            record = f'#{n}\n{m[2]}~\n{m[3]}~\n' + ' '.join(header) + '\n' + body
            section = section[:m.start()] + record + section[m.end():]
        text = prefix + '#ROOMS\n' + section
        targets = {k: state for k, state in reset_changes.items() if rooms[k[0]]['area'] == filename}
        if targets:
            def keep_reset(m):
                return '' if (int(m[1]), int(m[2])) in targets else m[0]
            text = re.sub(r'^D\s+0\s+(\d+)\s+(\d+)\s+\d+[^\n]*\n', keep_reset, text, flags=re.M)
            blocks = list(re.finditer(r'^#RESETS\n.*?^S$', text, re.M | re.S))
            assert blocks, filename
            pos = blocks[-1].end() - 1
            new = ''.join(f'D 0 {n} {d} {state}\n' for (n, d), state in sorted(targets.items()) if state is not None)
            text = text[:pos] + new + text[pos:]
        records(text)  # Validate serialized room coverage before writing any file.
        outputs[path] = text.replace('\n', '\r\n').encode() if b'\r\n' in raw else text.encode()

    result = {'rooms_changed': len(changed), 'areas_changed': sorted(files),
              'changes': changes,
              'room_metadata': [{'room': n, 'area': rooms[n]['area'], 'name': rooms[n]['name'],
                                 'before': {k: before[n][k] for k in ['flags', 'sector', 'copies']},
                                 'after': {k: rooms[n][k] for k in ['flags', 'sector', 'copies']}}
                                for n in sorted(changed) if any(rooms[n][k] != before[n][k] for k in ['flags', 'sector', 'copies'])],
              'door_resets': [{'room': n, 'direction': d, 'before': resets.get((n, d)), 'after': state}
                              for (n, d), state in sorted(reset_changes.items())]}
    print(json.dumps({'rooms_changed': len(changed), 'areas_changed': sorted(files),
                      'exit_changes': len(changes), 'reset_changes': len(reset_changes),
                      'reasons': dict(collections.Counter(c['reason'] for c in changes))}, indent=2))
    if write:
        for path, raw in outputs.items():
            path.write_bytes(raw)
        (ROOT / 'docs/world-map-repairs.json').write_text(json.dumps(result, indent=2) + '\n', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    repair(parser.parse_args().write)
