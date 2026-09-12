#!/usr/bin/env python3
"""Draft a reviewable interior catalogue, then apply the reviewed entries.

--draft creates the catalogue once, using the existing world as editorial input.
--apply checks every source room before changing descriptions, places, or B 1.
An already applied catalogue is a no-op; later world edits cause a conflict.
The JSON is the saved editorial source, not a runtime random text generator.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import random
import re
import string

import describe_world as world
from indoor_rooms import CATALOGUE_PATH, in_scope, room_kind
from indoor_scenes import SCENES, SURFACES
from indoor_landmarks import SPECIAL
from room_catalogue import RULES, EXACT, THEMES, TRAITS
from room_interiors import BY_ID, SUBAREA
import newbie_school

ROOT = Path(__file__).resolve().parents[1]
SIDES = ('near', 'far', 'left-hand', 'right-hand')
VEHICLE_SURFACES = ('charcoal vinyl', 'dull silver trim', 'burgundy upholstery',
                    'smoke-gray plastic', 'faded blue fabric', 'black rubber',
                    'tan leatherette', 'dark imitation wood')
OUTDOORS = {'air','exterior','roof','platform','forest','garden','shore','water','channel'}
FIXTURES = {
    'bedroom': ('bed',), 'living': ('sofa',), 'office': ('desk',),
    'kitchen': ('prep counter',), 'shop': ('counter',), 'library': ('reading table',),
    'dining': ('corner table',), 'cafe': ('counter','tables'),
    'tavern': ('bar','tables'), 'club': ('sofa',), 'foyer': ('waiting bench',),
    'workshop': ('worktable',), 'laboratory': ('workbench',),
    'treatment': ('treatment table',), 'clinic': ('waiting chairs',),
    'meeting': ('meeting table',), 'classroom': ('front desk','rear desks'),
    'studio': ('workstation',), 'laundry': ('folding counter',),
    'changing': ('bench',), 'spa': ('chaise',), 'theatre': ('audience seats',),
    'vehicle': ('seats',),
}

PLACE_TEXT = {k:v for _,_,places in RULES for k,v in places}
PLACE_TEXT.update({k:v for _,places in EXACT.values() for k,v in places})
PLACE_TEXT.update({k:v for _,places in BY_ID.values() for k,v in places})
PLACE_TEXT.update({
    'washbasin': 'The shallow basin has a rounded lip and a compact pair of fittings. '
        'A narrow ledge beside it offers room to rest a hand, with the mirror '
        'bringing the little washing space into close focus.',
    'treatment table': 'Firm padding covers a narrow, easily cleaned table. '
        'The raised surface leaves room to stand close on either side, '
        'keeping patient and attendant within quiet speaking distance.',
    'card table': 'A felt-covered top softens the little sounds of cards and chips. '
        'The padded rim offers a comfortable rest for an elbow, and the close '
        'seating keeps every small change of expression within view.',
})
TRANSIT_SEATS = ('The passenger seats fit closely inside the vehicle. Creased upholstery\n'
                 'holds a faint fabric smell, and the padded backs offer a compact place\n'
                 'to settle beside a traveling companion.')


def digest(text):
    return hashlib.sha256(text.encode('latin1')).hexdigest()


def read_world():
    for path in sorted((ROOT/'area').glob('*.are')):
        raw = path.read_bytes()
        text = raw.decode('latin1').replace('\r\n','\n')
        yield path, raw, text, world.records(text)


def context(name, body, kind):
    """Carry over established building character and explicit title traits."""
    if kind in OUTDOORS or kind in {'bare','vehicle'}:
        return ''
    additions = []
    for pattern, prose in TRAITS:
        if re.search(pattern, name, re.I):
            additions.append(prose)
            if len(additions) == 2:
                break
    for label, prose in THEMES.items():
        if label in name.casefold():
            additions.append(prose)
            break
    sub = re.search(r'^Y ([^~]*)~', body, re.M)
    if sub and sub[1].casefold() in SUBAREA:
        additions.append(SUBAREA[sub[1].casefold()])
    return ' '.join(additions)


def compose(kind, seed, labels):
    rng = random.Random(seed)
    scene = SCENES[kind]
    surface = rng.choice(VEHICLE_SURFACES if kind == 'vehicle' else SURFACES[scene['family']])
    values = {'side':rng.choice(SIDES), 'surface':surface}
    for parts in SCENES.values():
        for template in parts['focus']:
            for _, field, _, _ in string.Formatter().parse(template):
                if field and field not in values:
                    values[field] = '`w'+field+'`x' if field in labels else field
    washing = 'shower' if 'shower' in labels else 'washbasin'
    values['washing'] = '`w'+washing+'`x'
    prose = ' '.join(rng.choice(scene[part]).format_map(values)
                     for part in ('focus','detail','atmosphere'))
    return prose


def normalized(prose):
    return ' '.join(world.plain(prose).casefold().split())


def replacement(m, entry, filename):
    if entry['kind'] == 'tutorial':
        return m[0]
    body = world.PLACE.sub('', m[5])
    if filename != 'travel.are' and not re.search(r'^B\s',body,re.M):
        body = 'B 1\n'+body
    places = ''.join('P\n'+label+'~\n'+world.finish(prose)+'~\n'
                     for label,prose in entry['places'])
    body = re.sub(r'^S$', lambda _: places+'S', body, count=1, flags=re.M)
    return '#'+m[1]+'\n'+m[2]+'~\n'+world.finish(entry['description'])+'~\n'+m[4]+'\n'+body


def draft():
    if CATALOGUE_PATH.exists():
        raise SystemExit('Catalogue already exists; edit the reviewed JSON instead of replacing it.')
    source = [(path.name,m) for path,_,_,rooms in read_world() for m in rooms
              if in_scope(world.plain(m[2]),int(m[4].split()[1]),int(m[4].split()[2]))]
    old_counts = collections.Counter(normalized(m[3]) for _,m in source)
    entries, seen = {}, set()
    taxis = [compose('vehicle','taxi:'+str(i),('seats',)) for i in range(100)]
    assert len(set(map(normalized,taxis))) == 100
    for filename,m in source:
        name, vnum = world.plain(m[2]), int(m[1])
        key = f'{filename}:{vnum}'
        flags, sector = map(int,m[4].split()[1:])
        coords = re.search(r'^C ([^\n]+)', m[5], re.M)
        kind = room_kind(name,sector,coords[1] if coords else '')
        if kind == 'bathroom':
            labels = ('shower',) if flags & (1 << 24) else ('washbasin',)
        else:
            labels = FIXTURES.get(kind,())
        base = None
        if filename == 'limbo.are' and vnum in newbie_school.LESSONS:
            kind, prose = 'tutorial', ' '.join(m[3].split()).removesuffix('`x')
            places = [(p[1], ' '.join(p[2].split()).removesuffix('`x')) for p in world.PLACE.finditer(m[5])]
        elif key in SPECIAL:
            prose, labels = SPECIAL[key]
            places = [(k,PLACE_TEXT[k]) for k in labels]
        elif filename == 'travel.are' and name.casefold() == 'taxi':
            prose = taxis[vnum-19000]
            places = [(k,PLACE_TEXT[k]) for k in labels]
        else:
            # Keep already distinctive scenes and precise landmark descriptions.
            # Repeated landmarks receive additional local construction details.
            if (filename,vnum) in BY_ID:
                base, places = BY_ID[filename,vnum]
            elif name.casefold() in EXACT:
                base, places = EXACT[name.casefold()]
            elif old_counts[normalized(m[3])] == 1:
                base = ' '.join(m[3].split()).removesuffix('`x')
                places = [(p[1], ' '.join(p[2].split()).removesuffix('`x')) for p in world.PLACE.finditer(m[5])]
            if base:
                # Empty floor and performance space should not acquire seating
                # merely because a broad establishment name matched a lounge.
                if kind in {'performance','bare','hall','corridor','stairs'}:
                    places = []
                for attempt in range(1000):
                    prose = base
                    if attempt or old_counts[normalized(m[3])] > 1 or normalized(base) in seen:
                        rng = random.Random(key+':detail:'+str(attempt))
                        if old_counts[normalized(m[3])] > 40 or attempt >= 20:
                            prose += ' '+compose(kind,key+':landmark:'+str(attempt),tuple(k for k,_ in places))
                        else:
                            details = rng.sample(SCENES[kind]['detail'], min(2,len(SCENES[kind]['detail'])))
                            prose += ' '+' '.join(details)
                    if normalized(prose) not in seen:
                        break
                else:
                    raise ValueError('Exhausted landmark details: '+key)
            else:
                for attempt in range(10000):
                    prose = compose(kind,key+':'+str(attempt),labels)
                    extra = context(name,m[5],kind)
                    if extra:
                        prose += ' '+extra
                    if normalized(prose) not in seen:
                        break
                else:
                    raise ValueError('Exhausted scene combinations: '+key)
                places = [(k,PLACE_TEXT[k]) for k in labels]
        if filename == 'travel.are' and kind == 'vehicle':
            # Exact runtime stock marker permits safe cleanup when a transit
            # shell is subsequently reused for walking or another vehicle.
            places = [('seats', TRANSIT_SEATS)]
        # Every joinable feature must be visible in the room paragraph.
        mentions = {
            'counter': 'The `wcounter`x has a broad customer edge, rounded smooth where elbows have rested.',
            'tables': 'Small `wtables`x occupy the quieter margin, their tops softly marked by old cups and plates.',
            'rear desks': 'The `wrear desks`x form a close row behind the nearer seats, their tops carrying a fine web of idle scratches.',
        }
        for label,_ in places:
            if not all(word in world.plain(prose).lower() for word in label.lower().split()):
                prose += ' '+mentions[label]
        if normalized(prose) in seen:
            raise ValueError('Duplicate interior: '+key)
        seen.add(normalized(prose))
        entry = {'name':name,'kind':kind,'description':prose,'places':places,
                 'source_sha256':digest(m[0])}
        entry['applied_sha256'] = digest(replacement(m,entry,filename))
        entries[key] = entry
    data = {'version':1,'rooms':entries,'taxi_defaults':taxis}
    CATALOGUE_PATH.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
    print(f'Drafted {len(entries)} distinct room descriptions for review.')


def apply():
    data = json.loads(CATALOGUE_PATH.read_text(encoding='utf-8'))
    pending, conflicts, found = [], [], set()
    descriptions, places = set(), set()
    for path,raw,text,rooms in read_world():
        updates = {}
        for m in rooms:
            key = path.name+':'+m[1]
            entry = data['rooms'].get(key)
            if not entry:
                continue
            found.add(key)
            updated = replacement(m,entry,path.name)
            target_digest = digest(updated)
            if digest(m[0]) == target_digest:
                continue
            if digest(m[0]) not in (entry['source_sha256'],entry['applied_sha256']):
                conflicts.append(key)
                continue
            # Explicitly applying an edited catalogue accepts that prose while
            # still requiring the world to match the previously reviewed room.
            entry['applied_sha256'] = target_digest
            updates[m[1]] = updated
            descriptions.add(hashlib.sha256(world.finish(entry['description']).encode()).hexdigest())
            places.update(hashlib.sha256(('P\n'+label+'~\n'+world.finish(prose)+'~\n').encode()).hexdigest()
                          for label,prose in entry['places'])
        if updates:
            prefix, section = text.split('#ROOMS\n',1)
            changed = prefix+'#ROOMS\n'+world.ROOM.sub(lambda m:updates.get(m[1],m[0]),section)
            if world.structural_digest(text) != world.structural_digest(changed):
                raise ValueError('Structural mutation: '+path.name)
            pending.append((path,changed.replace('\n','\r\n' if b'\r\n' in raw else '\n').encode('latin1')))
    conflicts.extend(sorted(set(data['rooms'])-found))
    if conflicts:
        raise SystemExit('World changed since review; no files written: '+', '.join(conflicts))
    for path,raw in pending:
        path.write_bytes(raw)
    if pending:
        CATALOGUE_PATH.write_text(json.dumps(data,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
    managed_path = ROOT/'tools'/'room-description-managed.json'
    managed = json.loads(managed_path.read_text())
    managed['descriptions'] = sorted(set(managed['descriptions']) | descriptions)
    managed['places'] = sorted(set(managed['places']) | places)
    managed_path.write_text(json.dumps(managed,indent=2)+'\n')
    print(f'Applied reviewed interiors to {len(pending)} area files; all structural checks passed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--draft',action='store_true')
    action.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    draft() if args.draft else apply()
