#!/usr/bin/env python3
"""Apply the authored catalogue, or audit all shipped area rooms.

Run from any directory: python tools/describe_world.py --write / --check.
Only room descriptions, P place records, and B decoration ownership are changed.
Room identities, flags, coordinates, exits, resets, scripts, and feature data
remain intact.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import textwrap

from room_catalogue import TERRAIN, REALM_FORESTS, RULES, TRAITS, THEMES, EXACT
from room_interiors import BY_ID, SUBAREA
import newbie_school
from indoor_rooms import authored_room, in_scope

ROOT = Path(__file__).resolve().parents[1]
ROOM = re.compile(r'^#(\d+)\n([^~]*)~\n([^~]*)~\n([^\n]*)\n(.*?)(?=^#\d+\n)', re.M | re.S)
COLOR = re.compile(r'`(?:#[0-9a-fA-F]{6}|[0-9]{3}|.)')
PLACE = re.compile(r'^P\n([^~]*)~\n([^~]*)~\n', re.M)
PLACEHOLDER = re.compile(r'^(?:\s|`x)*(?:\(null\)|null|none|todo|tbd|test|placeholder|description|unfinished|under construction|room description|n/?a|\.+)?(?:\s|`x)*$', re.I)
COMPILED = [(re.compile(p, re.I), d, places) for p, d, places in RULES]
STOCK_NAMES = re.compile(r'^(?:(?:the |a )?(?:forest|skies|sky|air|atmosphere|ocean|water|underwater|under the ocean|under the river|grassy field|grass|field|coast|beach|bluffs|rocky ground|tunnels?|stone tunnel|sidewalk|alley|parking lot)|sector .*)$', re.I)

def plain(s):
    return COLOR.sub('', s).replace('`', '').strip()

def finish(s):
    return textwrap.fill(s.rstrip(' \n\r'), width=78, break_long_words=False, break_on_hyphens=False) + '`x\n'

def records(text):
    if '#ROOMS\n' not in text:
        return []
    section = text.split('#ROOMS\n', 1)[1]
    result = list(ROOM.finditer(section))
    expected = len(re.findall(r'^#(?!0\n)\d+\n', section.split('\n#0\n', 1)[0], re.M))
    if len(result) != expected:
        raise ValueError(f'Room parser coverage mismatch: {len(result)} != {expected}')
    for m in result:
        if not re.fullmatch(r'\d+\s+\S+\s+\d+', m[4]) or not m[5].rstrip().endswith('S'):
            raise ValueError(f'Malformed room {m[1]}')
    return result

def structural_digest(text):
    """Ignore prose, places and decoration ownership; retain exits and features."""
    if '#ROOMS\n' not in text:
        return hashlib.sha256(text.encode()).hexdigest()
    prefix, section = text.split('#ROOMS\n', 1)
    stripped = ROOM.sub(lambda m: '#'+m[1]+'\n'+m[2]+'~\n~\n'+m[4]+'\n'+re.sub(r'^B 1\n', '', PLACE.sub('', m[5]), flags=re.M), section)
    return hashlib.sha256((prefix+'#ROOMS\n'+stripped).encode()).hexdigest()

def describe(filename, m):
    if filename == 'limbo.are' and int(m[1]) in newbie_school.LESSONS:
        vnum = int(m[1])
        return newbie_school.description(vnum), newbie_school.places(vnum), 'newbie-school'
    name = plain(m[2])
    interior = authored_room(filename, int(m[1]), name)
    if interior:
        prose, places = interior
        return finish(prose), places, 'indoor-authored'
    sector = int(m[4].split()[-1])
    key = name.casefold()
    if (filename, int(m[1])) in BY_ID:
        prose, places = BY_ID[filename, int(m[1])]
        return finish(prose), places, 'bespoke'
    if not name or STOCK_NAMES.fullmatch(name):
        prose = REALM_FORESTS.get(filename, TERRAIN[23]) if sector == 23 else TERRAIN.get(sector, TERRAIN[0])
        return finish(prose), [], 'terrain'
    if key in EXACT:
        prose, places = EXACT[key]
        return finish(prose), places, 'bespoke'

    # In compound titles, the part following the establishment identifies the
    # room: House Red - Wine Cellar must not become an ordinary house.
    parts = re.split(r'\s+[-–]+\s+|:\s+', name)
    subject = parts[-1] if any(p.search(parts[-1]) for p, _, _ in COMPILED) else name
    subject = re.sub(r'^(?:in|inside|within|on|at)\s+(?:of\s+)?', '', subject, flags=re.I)
    head = re.split(r'\s+(?:with|within|overlooking|beside|near|of|beneath|above)\s+', subject, maxsplit=1, flags=re.I)[0]
    if any(p.search(head) for p, _, _ in COMPILED):
        subject = head
    matches = []
    for i, (pattern, prose, places) in enumerate(COMPILED):
        found = pattern.search(subject)
        if found:
            # Broad accommodation words are subordinate to a named room
            # function: a motel bathroom is a bathroom, not a bedroom.
            broad = pattern.pattern.startswith(('house|home|', 'bedroom|bedchamber|', r'\b(?:room|chamber|'))
            matches.append((10000 if broad else found.start(), i, prose, places))
    if matches:
        _, index, prose, places = min(matches)
        category = RULES[index][0]
    else:
        prose, places, category = TERRAIN.get(sector, TERRAIN[0]), [], 'sector-fallback'

    # Keep place keywords visible in the prose used by look. The labels are
    # also accepted directly by join through the existing is_name matcher.
    missing = [label for label, _ in places if not all(word in plain(prose).lower() for word in label.split())]
    if missing:
        prose += ' ' + ', '.join('`w'+label+'`x' for label in missing).capitalize() + (' provides' if len(missing) == 1 else ' provide') + ' a distinct place to gather.'

    # Write ordinary room prose, as Decorate description does, rather than
    # inserting a second room title into the paragraph.
    extras = [sentence for pattern, sentence in TRAITS if re.search(pattern, subject, re.I)]
    prose += (' ' + ' '.join(extras[:2])) if extras else ''
    exterior = bool(re.search(r'roof|sidewalk|parking|alley|outside|before|exterior|front of|window front|outskirts|walkway|path|street|avenue|highway|\broad\b|lawn|grass|garden|yard|forest|woods|beach|shore|\bsky\b', subject, re.I))
    if not exterior:
        for label, sentence in THEMES.items():
            if label in key:
                prose += ' ' + sentence
                break
        subarea = re.search(r'^Y ([^~]*)~', m[5], re.M)
        if subarea and subarea[1].casefold() in SUBAREA:
            prose += ' ' + SUBAREA[subarea[1].casefold()]
    return finish(prose), places, category

def color_errors(s):
    # New prose deliberately uses only portable one-character colours. Existing
    # title codes are out of scope and may contain RGB/256-colour sequences.
    errors = []
    for match in COLOR.finditer(s):
        if match[0] not in ('`w', '`g', '`c', '`b', '`y', '`r', '`x'):
            errors.append('unsupported colour '+match[0])
    if '`' in COLOR.sub('', s):
        errors.append('dangling colour introducer')
    if '`' in s and not s.rstrip().endswith('`x'):
        errors.append('missing final reset')
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    managed_path = ROOT/'tools'/'room-description-managed.json'
    managed = json.loads(managed_path.read_text()) if managed_path.exists() else {'descriptions': [], 'places': []}
    known_desc, known_places = set(managed['descriptions']), set(managed['places'])
    new_desc, new_places_hash = set(), set()
    active_files = set((ROOT/'area'/'area.lst').read_text().split()) - {'$'}
    report = {'rooms': 0, 'active_rooms': 0, 'decorated_rooms': 0, 'places': 0, 'files': {}, 'categories': collections.Counter(), 'errors': [], 'structural_sha256': {}}
    unique_descriptions = set()
    indoor_descriptions = collections.defaultdict(list)
    fallback = {}
    for path in sorted((ROOT/'area').glob('*.are')):
        raw = path.read_bytes()
        text = raw.decode('latin1').replace('\r\n', '\n')
        rooms = records(text)
        if not rooms:
            continue
        digest = structural_digest(text)
        report['structural_sha256'][path.name] = digest
        if args.write:
            prefix, section = text.split('#ROOMS\n', 1)
            def replace(m):
                if re.search(r'^B\s+1\s*$', m[5], re.M):
                    report['categories']['decorated-preserved'] += 1
                    return m[0]  # Player Decorate always has editorial priority.
                desc, places, category = describe(path.name, m)
                report['categories'][category] += 1
                if category == 'sector-fallback':
                    fallback[path.name+':'+m[1]] = plain(m[2])
                body = m[5]
                # Finished named locations have the same priority as a player
                # using Decorate. Only shared terrain stays regenerable.
                if category != 'terrain' and path.name != 'travel.are' and not re.search(r'^B\s', body, re.M):
                    body = 'B 1\n' + body
                old_generated = hashlib.sha256(m[3].encode()).hexdigest() in known_desc
                if old_generated:
                    body = PLACE.sub(lambda p: '' if hashlib.sha256(p[0].encode()).hexdigest() in known_places else p[0], body)
                if not PLACE.search(body) and (old_generated or PLACEHOLDER.fullmatch(m[3])):
                    new_places = ''.join('P\n'+key+'~\n'+finish(prose)+'~\n' for key, prose in places)
                    new_places_hash.update(hashlib.sha256(p[0].encode()).hexdigest() for p in PLACE.finditer(new_places))
                    body = re.sub(r'^S$', lambda _: new_places+'S', body, count=1, flags=re.M)
                # Preserve genuinely authored text if running against a later
                # world; this migration is safe to run repeatedly.
                if not PLACEHOLDER.fullmatch(m[3]) and not old_generated:
                    desc = m[3]
                else:
                    new_desc.add(hashlib.sha256(desc.encode()).hexdigest())
                return '#'+m[1]+'\n'+m[2]+'~\n'+desc+'~\n'+m[4]+'\n'+body
            text = prefix+'#ROOMS\n'+ROOM.sub(replace, section)
            if structural_digest(text) != digest:
                raise ValueError('Structural mutation: '+path.name)
            encoded = text.replace('\n', '\r\n' if b'\r\n' in raw else '\n').encode('latin1')
            if encoded != raw:
                path.write_bytes(encoded)
            rooms = records(text)
        report['files'][path.name] = len(rooms)
        report['rooms'] += len(rooms)
        if path.name in active_files:
            report['active_rooms'] += len(rooms)
        for m in rooms:
            unique_descriptions.add(m[3])
            report['decorated_rooms'] += bool(re.search(r'^B\s+1\s*$', m[5], re.M))
            location = path.name+':'+m[1]
            if in_scope(plain(m[2]), int(m[4].split()[1]), int(m[4].split()[2])):
                normalized = ' '.join(plain(m[3]).casefold().split())
                indoor_descriptions[normalized].append(location)
                if not authored_room(path.name, int(m[1]), plain(m[2])):
                    report['errors'].append(location+': missing interior catalogue entry')
            if PLACEHOLDER.fullmatch(m[3]) or len(plain(m[3])) < 40:
                report['errors'].append(location+': blank/placeholder/short description')
            for error in color_errors(m[3]):
                report['errors'].append(location+': '+error)
            places = list(PLACE.finditer(m[5]))
            report['places'] += len(places)
            if len(places) > 10:
                report['errors'].append(location+': more than 10 saved places')
            seen = set()
            for p in places:
                if any(word in p[1].lower() for word in ('shower', 'bath', 'jacuzzi', 'tub', 'pool')) and not (int(m[4].split()[1]) & (1 << 24)):
                    report['errors'].append(location+': bathing place lacks ROOM_BATHROOM')
                if not p[1].strip() or not p[2].strip() or PLACEHOLDER.fullmatch(p[2]):
                    report['errors'].append(location+': empty place')
                for word in p[1].lower().split():
                    if word in seen:
                        report['errors'].append(location+': ambiguous join keyword '+word)
                    seen.add(word)
                if not all(word in plain(m[3]).lower() for word in p[1].lower().split()):
                    report['errors'].append(location+': place not discoverable in description: '+p[1])
                for error in color_errors(p[2]):
                    report['errors'].append(location+': place '+error)
    out = ROOT/'docs'/'room-description-audit.json'
    duplicates = [locations for locations in indoor_descriptions.values() if len(locations) > 1]
    for locations in duplicates:
        report['errors'].append('Duplicate indoor description: '+', '.join(locations))
    report['indoor_rooms'] = sum(map(len, indoor_descriptions.values()))
    report['unique_indoor_descriptions'] = len(indoor_descriptions)
    report['duplicate_indoor_groups'] = len(duplicates)
    report['unique_descriptions'] = len(unique_descriptions)
    if args.write:
        managed_path.write_text(json.dumps({'descriptions': sorted(new_desc | known_desc), 'places': sorted(new_places_hash | known_places)}, indent=2)+'\n')
        (ROOT/'docs'/'room-description-fallbacks.json').write_text(json.dumps(fallback, indent=2)+'\n')
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('structural_sha256','categories','files','errors')}, indent=2))
    print('Errors:', len(report['errors']))
    print('\n'.join(report['errors'][:30]))
    return bool(report['errors'])

if __name__ == '__main__':
    raise SystemExit(main())
