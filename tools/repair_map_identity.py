#!/usr/bin/env python3
"""Reviewed physical-map repairs; no market or door normalization. Dry run by default."""
import argparse
import collections
import json
import re
import textwrap

from audit_world_map import ROOT, read_world, physical_findings
from audit_institute import EXIT
from describe_world import records, plain, PLACE

# All have zero incoming exits and no saved room references. Their coordinates
# are already represented by a connected room; these are obsolete copies.
OBSOLETE = {1842, 137281, 137283, 137285, 137286, 137287, 137289,
            137290, 137292, 137293, 137295, 137284, 137288, 137291, 137294,
            *range(73930, 73942)}
ROOF_PROSE = [
    'The exposed roof forms a solid surface beneath the open sky. Weathered seams '
    'and patches divide the roofing into uneven sections, with grit gathered along '
    'the raised edges. The building lies beneath this level; beyond its outline, '
    'the surrounding air opens away from the roof.',
    'A broad stretch of roofing carries the wear of sun, rain, and older repairs. '
    'The firm surface changes texture around its seams, and loose grit collects '
    'where the finish meets a raised edge. There is no ceiling overhead, only the '
    'open sky above the building.',
    'The top of the building spreads into a weathered roof surface. Faint channels '
    'and overlapping repairs interrupt the otherwise plain expanse, with rougher '
    'patches near the edges. Solid roofing supports this level while the open air '
    'beyond the building makes the height apparent.'
]
CAVE_PROSE = [
    'Rough stone encloses the underground space, its uneven surface broken by '
    'seams and shallow recesses. Loose grit gathers beneath the lower edges, and '
    'the ground feels firm beneath the scattered fragments. The air is close and '
    'mineral-cool, carrying sounds against the surrounding rock instead of into '
    'the open street above.',
    'The cavern extends beneath the surface in irregular folds of rock. Small '
    'fragments collect where the floor meets the rough sides, and darker seams '
    'trace the stone overhead. A cool mineral smell hangs in the still air. The '
    'enclosing surfaces give even small movements a short, close echo.'
]


def repair(write=False):
    rooms = read_world()
    findings = physical_findings(rooms)
    edits = collections.defaultdict(dict)
    log = []
    for f in findings:
        n = f['vnum']
        if f['kind'] == 'roof_named_sky':
            edits[n]['name'] = '`wAn Exposed Rooftop`x'
            edits[n]['description'] = textwrap.fill(ROOF_PROSE[n % len(ROOF_PROSE)], 78) + '`x\n'
        elif f['kind'] == 'solid_floor_named_sky':
            edits[n]['name'] = '`wThe Upper Floor`x'
            edits[n]['description'] = textwrap.fill(
                'A solid upper floor occupies this part of the building. Its surface '
                'runs between the structural edges, with small changes in texture '
                'around the joins. The space has a plain, unfinished character, its '
                'proportions defined by the floor and surrounding construction rather '
                'than any particular furnishings.', 78) + '`x\n'
        elif f['kind'] == 'cave_named_after_surface':
            level = 'Upper' if rooms[n]['coords'][2] == -1 else 'Lower'
            edits[n]['name'] = f'`wThe {level} Caverns`x'
            edits[n]['description'] = textwrap.fill(CAVE_PROSE[n % len(CAVE_PROSE)], 78) + '`x\n'
        elif f['kind'] == 'wrong_adjacent_destination':
            assert (n, f['direction'], f['expected']) in {
                (131622, 4, 9775), (131734, 4, 9601),
                (197697, 4, 114108), (197699, 4, 114106)}
            edits[n].setdefault('exits', {})[f['direction']] = f['expected']
        else:
            continue
        log.append(f)
    removed = OBSOLETE & rooms.keys()
    for n, r in rooms.items():
        for e in r['exits'].values():
            assert e['to'] not in removed, ('Still referenced', n, e['to'])
    for n in removed:
        log.append({'kind': 'remove_unreferenced_duplicate', 'vnum': n,
                    'area': rooms[n]['area'], 'name': rooms[n]['name'], 'coords': rooms[n]['coords']})
    if not edits and not removed:
        print('Reviewed physical-map repairs are already applied.')
        return
    outputs = {}
    for area in {rooms[n]['area'] for n in set(edits) | removed}:
        path = ROOT / 'area' / area
        raw = path.read_bytes()
        text = raw.decode().replace('\r\n', '\n')
        prefix, section = text.split('#ROOMS\n', 1)
        for m in reversed(records(text)):
            n = int(m[1])
            if n in removed:
                replacement = ''
            elif n in edits:
                e = edits[n]
                body = m[5]
                if 'description' in e:
                    # Remove surface furniture/place prose copied into these generic
                    # roof/cave rooms; room features and other metadata remain intact.
                    body = PLACE.sub('', body)
                    if not re.search(r'^B 1$', body, re.M):
                        body = 'B 1\n' + body
                if 'exits' in e:
                    def redirect(x):
                        if int(x[1]) not in e['exits']:
                            return x[0]
                        return (f'D{x[1]}\n{x[2]}~\n{x[3]}~\n{x[4]} {x[5]} '
                                f'{e["exits"][int(x[1])]}\n{x[7]}\n')
                    body = EXIT.sub(redirect, body)
                replacement = (f'#{n}\n{e.get("name", m[2])}~\n'
                               f'{e.get("description", m[3])}~\n{m[4]}\n{body}')
            else:
                continue
            section = section[:m.start()] + replacement + section[m.end():]
        text = prefix + '#ROOMS\n' + section
        records(text)
        outputs[path] = text.replace('\n', '\r\n').encode() if b'\r\n' in raw else text.encode()
    print(json.dumps({'changed_rooms': len(edits), 'removed_duplicate_rooms': len(removed),
                      'findings': dict(collections.Counter(f['kind'] for f in log))}, indent=2))
    if write:
        for path, raw in outputs.items():
            path.write_bytes(raw)
        report = ROOT / 'docs/map-identity-repairs.json'
        previous = json.loads(report.read_text()) if report.exists() else []
        report.write_text(json.dumps(previous + log, indent=2) + '\n', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    repair(parser.parse_args().write)
