"""Saved interior coverage and the per-room editorial catalogue.

Legacy sectors sometimes disagree with room names. Coverage is deliberately
inclusive; a roof marked indoors still receives outdoor prose. Runtime transit
shells are recorded here but retain their automatic ownership policy.
"""
import json
from pathlib import Path
import re

INDOOR_SECTORS = {0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 14, 15, 16, 17, 24}
INTERIOR_NAME = re.compile(
    r'\b(?:bedroom|bedchamber|bathroom|restroom|washroom|kitchen|kitchenette|'
    r'lounge|parlor|parlour|office|classroom|laboratory|library|hallway|corridor|'
    r'stairwell|basement|cellar|warehouse|workshop|storeroom|stockroom|attic|'
    r'locker room|dressing room|living room|dining room|hotel room|motel room|'
    r'reception|foyer|auditorium|chapel|dormitory|barracks|apartment|airlock)\b',
    re.I)
CATALOGUE_PATH = Path(__file__).with_name('indoor-room-descriptions.json')
BROAD_INTERIOR_NAME = re.compile(
    r'\b(?:room|tavern|bar|shop|store|cafe|diner|clinic|toilets|restrooms|lobby|'
    r'theater|theatre|motel|hotel|cabin|house|hut|chalet|restaurant|club|saloon|'
    r'inn|palace|castle|manor|mansion|bunker|crypt|cave|cavern|tunnel|barn|stable|'
    r'studio|elevator|shopfront|cafeteria|pub|gymnasium|gym|antechamber)\b', re.I)


def in_scope(name, flags, sector):
    if flags & 8 or sector in INDOOR_SECTORS or INTERIOR_NAME.search(name):
        return True
    if re.search(r'\b(?:outside|exterior|behind|sidewalk|alley|alleyway|path|trail|drive|'
                 r'cobblestones|approach|maze|ruins|firepit|awning|roof|rooftop|rooftops)\b|cul-de-sac', name, re.I):
        return False
    return bool(BROAD_INTERIOR_NAME.search(name) and room_kind(name,sector) not in
                {'air','exterior','roof','platform','forest','garden','shore','water','channel'})


def room_kind(name, sector, coordinates=''):
    text = name.casefold()
    if re.search(r'bathroom|\bshowers?\b|restroom|washroom', text):
        return 'bathroom'
    if re.search(r'operating theat(?:er|re)', text):
        return 'treatment'
    if 'opera house' in text:
        return 'theatre'
    if 'elevator' in text:
        return 'airlock'
    if re.search(r'submerged|aquatic cavern', text):
        return 'water'
    if re.search(r'entrance (?:of|to) a cave', text):
        return 'cave'
    if re.search(r'top of .*airlock|top chamber of the jungle gym', text):
        return 'platform'
    if re.search(r'\bgrave\b|graveyard|cemetery', text):
        return 'exterior'
    if 'loving kitchen - back of house' in text:
        return 'kitchen'
    if 'swimming pool' in text:
        return 'pool'
    # In compound names, classify the actual room before its establishment.
    # A sidewalk in front of a lounge is still a sidewalk.
    parts = re.split(r'\s+-+\s+|:\s+', text)
    if len(parts) > 1:
        text = parts[-1]
    head = re.split(r'\s+(?:of|within|beside|near|beneath|above|overlooking|in|with|behind)\s+', text, maxsplit=1)[0]
    if (INTERIOR_NAME.search(head) or BROAD_INTERIOR_NAME.search(head) or
        re.search(r'\b(?:forest|forested|backyard|garden|sidewalk|road|street|alley|roof|rooftop|porch|deck|balcony|platform|path|lot|stairs|stair|staircase|walkway|channel|sky|skies|hall|floor|tent|arena|bowling|arcade|interior|grotto|loft|entry|checkout|shopping|backstage|tunnels|exterior|front)\b|semi-covered', head)):
        text = head
    has = lambda pattern: bool(re.search(pattern, text))
    if has(r'\b(?:grass|grassy|lawns?|meadow|park|gardens?|biome|grove|biodome|greenhouse)\b') and not has(r'airlock|catwalk|office|stairs'):
        return 'garden'
    if has(r'\b(?:sidewalk|streets?|road|avenue|boulevard|path|pathway|footpath|alley|alleyway|driveway|patio|outdoor|outside|lot|outskirts|rubble|exterior|backyard)\b|\bfront of|window front|^the dumpster|semi-covered|^sector (?:alley|rocky|cemetery)$'):
        return 'exterior'
    if has(r'\b(?:waters|water|lagoon|harbor|seas)\b'):
        return 'water'
    if has(r'\b(?:cove|coast)\b'):
        return 'shore'
    if has(r'\b(?:sky|air|skies|nothingness|abyss)\b|^a chandelier'):
        return 'air'
    if has(r'\b(?:balcony|porch|porche|deck|platform|gazebo|gazeebo)\b'):
        return 'platform'
    if not text or has(r'^(?:delete|test|sector \d+)$|under development|undesignated|unfurnished|featureless|vacant|\bempty\b'):
        return 'bare'
    if has(r'^outside\b|^before\b|\bparking\b|\bcarport\b|gas pumps|\blawn\b|\byard\b|\bplaza\b|\bcourtyard\b'):
        return 'exterior'
    if has(r'\broof\b|\brooftop\b') and not has(r'rooftop (?:apartment|bedroom|studio|suite)'):
        return 'roof'
    if has(r'\bskies\b|\bsky\b|\batmosphere\b|^above\b|\btreetops\b'):
        return 'air'
    if has(r'\b(?:forest|woods|grove|woodland|thicket)\b'):
        return 'forest'
    if has(r'\b(?:beach|shore|coast|sands)\b'):
        return 'shore'
    if has(r'\b(?:garden|biodome|greenhouse|arboretum)\b') and not has(r'lab|airlock|catwalk|stairs|staircase'):
        return 'garden'
    if has(r'\b(?:sidewalk|street|road|avenue|boulevard|quay)\b') and not INTERIOR_NAME.search(text):
        return 'exterior'
    if has(r'\b(?:bridge|pier|dock|porch|porche|balcony|terrace|veranda|overlook|boardwalk|railing)\b') and not has(r'office|bedroom|suite|living room|recreation|observation deck'):
        return 'platform'
    if has(r'center channel'):
        return 'channel'
    if has(r'underwater|under the water|under the ocean|\bocean\b|\briver\b|\bbay\b|\blake\b|\btrench\b') and not INTERIOR_NAME.search(text):
        return 'water'
    if has(r'shower|bathroom|restroom|washroom|lavator|\btoilets\b|\btoilet\b|\bouthouse\b|steam room|\bbath\b'):
        return 'bathroom'
    if has(r'operating theater|operating theatre|surgery|surgical|treatment room|examination|diagnosis|intervention|fleshforming|patient room|hospital room'):
        return 'treatment'
    if has(r'kitchen displays|bedroom displays|living room displays|dining room displays|office displays|outdoor displays'):
        return 'showroom'
    if has(r'bedroom|bedchamber|sleeping|guestroom|guest room|guest suite|residential suite|staff cots|\bbunk|dormitory|barracks|\broom (?:\d|one|two|three|four|five|six)|^(?:rook|bishop|kingson|queenson) \d|motel room|hotel room|servant quarters|private (?:room|chamber)|cabana') and not has(r'staff offices'):
        return 'bedroom'
    if has(r'kitchen|kitchenette|prep area|mess hall|canteen'):
        return 'kitchen'
    if has(r'pantry|larder|freezer|refrigerated|coolers'):
        return 'pantry'
    if has(r'locker|changing room|dressing room|changing booth'):
        return 'changing'
    if has(r'office|\bstudy\b|chambers|command center|bullpen|operator|cockpit|projection booth|librarian.*desk'):
        return 'office'
    if has(r'meeting|conference|council|senate|court room|courtroom'):
        return 'meeting'
    if has(r'library|bookstore|book store|\bstacks\b|reading|archives|book nook|comics|obscure titles|shelves|athenaeum|bibliotheque'):
        return 'library'
    if has(r'classroom|latin room|\blesson\b|forensics classroom'):
        return 'classroom'
    if has(r'laboratory|labratory|\blab\b|experimentation|experiments|diagnostics|quality assurance|research'):
        return 'laboratory'
    if has(r'clinic|hospital|medical|recovery|\bward\b|sanitarium'):
        return 'clinic'
    if has(r'\bcell\b|\bcells\b|prison|dungeon|holding pen|\bcage\b|interrogation'):
        return 'cell'
    if has(r'chapel|church|cathedral|temple|shrine|ritual|confession|sanctum'):
        return 'chapel'
    if has(r'museum|gallery|exhibit|diorama|aquarium|arcane viewing') or 'museum' in name.casefold():
        return 'gallery'
    if has(r'workshop|workroom|work area|atelier|painting studio|painting room|art room|artist|kiln|sewing|printing press'):
        return 'workshop'
    if has(r'computer|digital media|recording|music room|music studio|photo lab|filming|radio room|dj booth|design studio'):
        return 'studio'
    if has(r'laundry|laundromat'):
        return 'laundry'
    if has(r'foyer|lobby|reception|entry hall|entryway|check.in|check-in|terminal|airport|\bstation\b|depot|entrance|entry|mudroom'):
        return 'foyer'
    if has(r'stairs?|staircase|stairwell|steps|landing|fire.escape|\bladder\b|catwalk|clocktower|lighthouse stairs|bell tower'):
        return 'stairs'
    if has(r'hallway|corridor|passageway|walkway|passage|first floor|second floor|third floor|mezzanine'):
        return 'underground' if coordinates.split()[-1:] == ['-1'] else 'corridor'
    if has(r'ballroom|dance floor|\bstage\b|rehearsal|mosh pit'):
        return 'performance'
    if has(r'backstage'):
        return 'living' if has(r'lounge') else 'storage'
    if has(r'ice.cream parlor|pizza joint'):
        return 'cafe'
    if has(r'living room|living space|living area|\blounge\b|parlor|parlour|common room|recreation|\bden\b|breakroom|break room|leisure|apartment|\bflat\b|\bloft\b'):
        return 'living'
    if has(r'\bbar\b|tavern|\bpub\b|saloon|hookah'):
        return 'tavern'
    if has(r'cafe|coffee|doughnut|\bdiner\b|tea party'):
        return 'cafe'
    if has(r'dining|restaurant|resteraunt|cafeteria|banquet|cuisine|pancakes|pizza hut|\bkfc\b'):
        return 'dining'
    if has(r'ballroom|dance floor|stage|rehearsal|mosh pit'):
        return 'performance'
    if has(r'\bclub\b|discotheque|\brave\b|dance'):
        return 'club'
    if has(r'theatre|theater|auditorium|amphitheater|concert|planetarium'):
        return 'theatre'
    if has(r'gym|fitness|dojo|fencing|arena|dueling|fighting pit|shooting|archery|bowling|billiard|pool tables|arcade|\brink\b|sports|bleachers|weight room|smash room|sport facilities'):
        return 'recreation'
    if has(r'\bpool\b'):
        return 'pool'
    if has(r'\bspa\b|massage|beauty|zen-tasies'):
        return 'spa'
    if has(r'steel mill'):
        return 'mill'
    if has(r'warehouse|hangar|shipping container|loading dock|receiving area'):
        return 'warehouse'
    if has(r'storage|stockroom|storeroom|closet|shed|back room|utility|supply|maintenance|mailroom|sorting|evidence'):
        return 'storage'
    if has(r'\bshop\b|\bstore\b|storefront|market|bazaar|bizaar|display|department|apparel|clothing|fashion|jewelry|jewelers|jewellery|novelt|accessories|supplies|pharmacy|\bmall\b|\bpawn\b|costume|counter|checkout|shopping|hardware|snacks|cold drinks|firearms|personal defen[cs]e|lingerie|attire|sundries|live bait|shoes section'):
        return 'shop'
    if has(r'basement|cellar|celler|catacomb|sewer|\btunnel\b|tunnels|\bwell\b|underbelly|winding tubes'):
        return 'underground'
    if has(r'\btaxi\b|\bcar\b|\btrolly\b|\bford\b|\bchevy\b|\bbuick\b|\blotus\b|\bhonda\b'):
        return 'vehicle'
    if has(r'boat|aboard|ship|sloop|freighter|ketch|airplane|\bbus\b|\btrain\b'):
        return 'vessel'
    if has(r'cave|cavern|grotto|crevice|\bmine\b|\bpit\b|tumulus|tomb|mausoleum|\bdepths\b'):
        return 'cave'
    if has(r'\bhall\b'):
        return 'hall'
    if has(r'\bhouse\b|\bhome\b|cottage|chalet|residence|lodgings|\binn\b|hotel|motel|\bvilla\b|\bmanor\b|mansion|\bcabin\b|estate'):
        return 'living'
    if has(r'\btent\b|encampment|\bcamp\b|lean.to'):
        return 'camp'
    if has(r'elevator|airlock|decontamination'):
        return 'airlock'
    if has(r'\bbank\b|\bvault\b'):
        return 'bank'
    if has(r'gravesend high'):
        return 'hall'
    return {0:'bare',2:'living',3:'club',4:'dining',5:'shop',6:'tavern',8:'warehouse',
            9:'hall',11:'underground',12:'cafe',14:'underground',15:'clinic',16:'bank',
            17:'vehicle',18:'air',20:'water',21:'water',22:'air',23:'forest',24:'cave',
            26:'shore',28:'water',29:'exterior',30:'exterior'}.get(sector,'hall')


def load_catalogue():
    if not CATALOGUE_PATH.exists():
        return {}
    return json.loads(CATALOGUE_PATH.read_text(encoding='utf-8'))['rooms']


ROOMS = load_catalogue()


def authored_room(filename, vnum, name):
    entry = ROOMS.get(f'{filename}:{vnum}')
    # A later room rename should not silently acquire an unrelated old interior.
    if entry and entry['name'] == name:
        return entry['description'], [tuple(place) for place in entry['places']]
    return None
