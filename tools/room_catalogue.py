"""Authored room vocabulary shared by the area migration and C++ terrain fallback.

No exits are inferred from names. Furniture described by a place is implemented
as a P record, not as an object, shop, container, or equipment provider.
"""

TERRAIN = {
0: "A plain floor meets unadorned walls around a clear central space. The restrained surroundings leave little to distract from anyone sharing the room.",
1: "`wWorn pavement`x forms the road surface, it's patched seams and scuffed edges recording years of traffic. The traveled ground stays open between the rougher margins.",
2: "Plastered walls enclose a modest domestic interior. A scuffed floor leaves a clear central area, with the quieter edges of the room set apart from the space used for passing through.",
3: "A broad `wdance floor`x occupies the middle of the club. Dark finishes soften the surrounding walls, while a seating area sits back from the open floor.",
4: "Dining tables divide the room into small islands of conversation. Wipe-clean surfaces and well-worn chair legs give the dining area a practical, familiar character.",
5: "Rows of displays organize the shop floor, leaving space to browse between them. A `wcounter`x marks the edge of the customer area; scuffs near it's base show where people linger.",
6: "A long `wbar counter`x anchors the room, it's worn edge smoothed by countless elbows. Tables occupy the remaining floor, with space between them for small groups to gather.",
7: "Hard walls hem in a strip of scuffed paving. Grit collects along the edges of the `walley`x, where the ground receives less wear than the narrow middle.",
8: "Broad spans of industrial flooring lie beneath structural beams. Scratches and old handling marks break up the plain surfaces, giving the open warehouse space a thoroughly practical character.",
9: "Durable flooring and plain walls give this commercial interior an orderly appearance. The center remains open, with the margins arranged to keep people out of the main circulation space.",
10: "`gGrass`x covers the open ground in uneven layers. Shorter growth marks the more exposed patches, while the thicker edges gather fallen stems and seed husks.",
11: "Rough `wstonework`x encloses the tunnel. Worn seams run along it's sides, and grit gathers where the walls meet the floor; the confined space makes nearby movement sound close.",
12: "Small tables bring the cafe down to the scale of a quiet conversation. A `wcounter`x faces the seating area, with hard flooring worn smooth where customers gather.",
13: "Seams and patches break up the exposed roof surface. The building's broad upper span provides little enclosure, and it's weathered materials show the wear of an elevated position.",
14: "The building's lower structure is exposed here in heavy walls and a plain floor. Corners feel close beneath the ceiling, and small sounds carry through the enclosed basement.",
15: "Hard, washable surfaces define the clinical space. Pale walls and an uncluttered floor give the room a deliberate order, with an edge of antiseptic in the air.",
16: "Restrained finishes and durable flooring lend the public interior a formal air. The broad central space leaves room for people to wait without crowding the margins.",
17: "Upholstered seats fit tightly within the vehicle's metal body. The compact passenger space carries the familiar smells of fabric, rubber, and enclosed travel.",
18: "The `cair`x stretches around an unbounded space above the ground. There is no floor or surrounding wall here; distance and height give the emptiness it's scale.",
19: "Irregular ground gathers around the `rhellgate`x, it's edges harsh against the surrounding space. The threshold dominates the scene, making everything close to it feel provisional.",
20: "`cWater`x fills the surrounding expanse, it's overlapping surface textures concealing the depth beneath. There is no solid footing in this stretch of open water.",
21: "Water encloses the space on every side. Suspended particles soften it's depth, and the `bsubmerged surroundings`x merge into an indistinct distance.",
22: "A vast reach of `cupper air`x surrounds this exposed height. With no enclosing surfaces, the space has the disorienting scale of open atmosphere.",
23: "`gTree trunks`x crowd the uneven forest floor. Roots break through a layer of old leaves and fallen twigs, while overlapping branches divide the woodland into close, irregular spaces.",
24: "Uneven `wrock`x forms the cave's walls and floor. Natural seams interrupt the stone, and loose fragments collect in shallow pockets along it's base.",
25: "Soft mud lies between tangled roots and coarse wetland growth. Dark water occupies the lower patches of the `gswamp`x, breaking the ground into uncertain pieces.",
26: "Loose `ysand`x forms a broad, yielding surface. Finer grains collect between scattered shell fragments, while the exposed ground bears faint ridges and worn depressions.",
27: "Broken `wstone`x and rough outcrops interrupt the ground. Thin deposits of grit settle in the cracks, leaving the harder surfaces exposed and uneven underfoot.",
28: "`cShallow water`x spreads over a submerged bed of sediment. The bottom remains close beneath the surface, it's texture softened by layers of water and fine silt.",
29: "A strip of `wsidewalk`x provides firm footing. It's paving is worn through the middle, with seams and small chips collecting grit along the less-traveled edges.",
30: "A broad parking surface opens around worn bay markings. Tire scuffs and patched pavement distinguish the vehicle spaces from the rougher margins of the lot.",
31: "Rows of `wgrave markers`x interrupt the cemetery ground. Their stone surfaces vary in wear, while the spaces between them lend the burial ground a measured, solemn rhythm.",
32: "Compacted `yearth`x forms the traveled ground. Small stones press into it's surface, and looser soil gathers along the edges where fewer feet have passed.",
}

REALM_FORESTS = {
'otherfor.are': "Ancient `gtrees`x rise from a deep mat of roots and moss. Their immense trunks crowd unfamiliar plants, whose curling leaves and intricate shapes make the forest seem almost recognizable, yet never quite familiar.",
'godfor.are': "Widely spaced `gtrees`x rise above soft grass and naturally ordered flower beds. Their clean-limbed shapes give the woodland a strange composure, as though each trunk had grown with room deliberately left for it's neighbors.",
'wildfor.are': "Massive `gtrunks`x rise through tangled undergrowth. Thick roots buckle the soil, and layers of vines and fallen timber turn the forest floor into a dense, muscular tangle.",
'hellfor.are': "Knotted `wtrees`x twist above a litter of splintered branches. Swollen burls suggest faces in the bark, and the interlocking trunks break the forest into cramped, unsettling pockets.",
}

TRANSIT = [
    'Hard panels enclose a compact subway carriage. Metal handholds border a narrow standing aisle, while a line of `wseats`x occupies the edge of the passenger space.',
    "A narrow `wseat`x defines the riding position. The space is open to it's surroundings, with little enclosure between the rider and the passing environment.",
    'A worn strip of `yearth`x lies among close-set forest trunks. Roots interrupt the path surface, and fallen leaves collect along the less-traveled margins beneath the branches.',
]

# Ordered by room function, before the broader sector classification.
# (pattern, prose, place keyword + description pairs)
RULES = []
def rule(pattern, prose, *places):
    RULES.append((pattern, prose, list(places)))

rule(r'underwater|submerged|under (?:the )?(?:ocean|water|waves)|watery depths', TERRAIN[21])
rule(r'\b(?:skies|sky|atmosphere|treetops)\b|^above (?:the arena|cage|magical)', TERRAIN[18])
rule(r'\b(?:roof|rooftop)\b|atop a covered walkway', TERRAIN[13])
rule(r'\b(?:sidewalk|pavement)\b', TERRAIN[29])
rule(r'parking|carport', TERRAIN[30])
rule(r'\b(?:alley|alleyway)\b', TERRAIN[7])
rule(r'\b(?:outside|before|exterior|front of|behind a .*store|window front|outskirts)\b', "The ground here forms an approach beside the surrounding structure. Wear concentrates in the open standing space, while grit settles against the building's base.")
rule(r'\b(?:stairs|staircase|stairwell|steps|landing|wooden stair|fire.escape)\b', "Repeated treads and worn edges define the stair structure. The landing provides a small level space within it's close-set framework.", ('landing', 'The landing offers a level place to stand beside the stair structure, clear of the treads.'))
rule(r'\b(?:hallways?|corridors?|passageways?|entry corridor|office corridor)\b', "Plain walls border a strip of hard flooring. Wear follows the middle of the corridor, while it's margins remain quiet and comparatively untouched.")
rule(r'\b(?:walkway|footpath|pathway|trail|path|promenade)\b', "A worn strip of ground marks the path through it's surroundings. Small irregularities break up the surface, and the less-traveled margins retain a rougher texture.")
rule(r'\b(?:streets?|avenue|highway|road|lane|parkway|boulevard|drive|row)\b|crossroads|intersection', TERRAIN[1])
rule(r'\b(?:lawns?|grassy|grass|meadow|fields?|grounds|yard|perimeter)\b', TERRAIN[10])
rule(r'\b(?:gardens?|greenhouse|biodome|arboretum)\b', "Beds of cultivated plants divide soil into smaller, carefully tended spaces. Leaf shapes overlap above the earth, giving the planted area a texture quite different from the ground around it.", ('planting beds', 'The edges of the planting beds offer a close view of stems, leaves, and the worked soil around their roots.'))
rule(r'\b(?:forest|woods|wood|jungle|grove)\b', TERRAIN[23])
rule(r'\b(?:beach|shore|shoreline|sands|dunes)\b', TERRAIN[26])
rule(r'\b(?:ocean|bay|river|lake|pond|water|waters|sea|moat|lagoon|reservoir|shallows)\b', TERRAIN[20])
rule(r'\b(?:bluffs|cliff|cliffs|mountains|mountain|peaks|rocky|headlands)\b', TERRAIN[27])
rule(r'\b(?:cemetery|cemetary|graveyard)\b', TERRAIN[31])
rule(r'\b(?:swamp|swamps|bog|mire)\b', TERRAIN[25])
rule(r'\b(?:tunnel|tunnels|sewer|sewers|catacombs)\b', TERRAIN[11])
rule(r'\b(?:cave|cavern|grotto|crevice)\b', TERRAIN[24])
rule(r'\b(?:empty|unfurnished|bare|featureless|vacant|undesignated|development|construction|renovations|transition|delete|test)\b', "Unoccupied space lies within plain, unfinished surfaces. Scuffs and small imperfections remain exposed, giving the area the quiet, stripped-back character of a place without furnishings.")
rule(r'bathroom|restroom|washroom|lavatory|lavatories|toilets|outhouse', "Hard surfaces and close-set fittings give the washroom a compact layout. A `wshower`x occupies one side, with a screened washing space and a drain beneath the fittings.", ('shower', 'Water runs from the shower head into a drained washing space, with room to stand beneath the spray.'))
rule(r'shower|steam room', "Washable surfaces enclose the `wshower`x. Drainage grooves interrupt the floor beneath the fixtures, and mineral traces mark the places reached by water.", ('shower', 'Water sprays from the shower fixtures across the tiled washing space and runs into the floor drains.'))
rule(r'locker|changing room|dressing room|changing booth|costumery', "A clear changing space occupies the center, bordered by places to set clothing aside. A `wbench`x keeps the seating close to the wall and leaves the main floor free.", ('bench', 'The bench provides a narrow seat beside the changing space.'))
rule(r'bedroom|bedchamber|sleeping|guestroom|guest room|guest suite|residential suite|hotel.*room|motel room|bunk|dormitory|quarters|barracks|^room [0-9]|^(?:kingson|queenson|bishop|rook) [0-9]', "A `wbedside area`x defines the room's quieter half. Sleeping furniture sits clear of a small standing space, and the surrounding walls give the interior a close, private scale.", ('bedside', 'There is room to sit or stand beside the sleeping area, close enough for quiet conversation.'))
rule(r'kitchen|kitchenette|prep area|canteen|mess hall', "Work surfaces follow the room's edges, leaving the center clear for preparing food. The `wprep counter`x bears small marks of use, and hard flooring makes the practical layout easy to keep orderly.", ('prep counter', 'A clear stretch of work surface offers room to stand beside the preparation area.'))
rule(r'pantry|larder|freezer|cold goods|refrigerated', "Storage shelves arrange the enclosed space into narrow rows. Plain surfaces and a clear central standing area keep the room's practical purpose apparent.", ('shelves', 'The shelves border a small standing space where stored supplies can be examined.'))
rule(r'living room|living space|living area|lounge|parlor|parlour|common room|recreation|\bden\b', "A `wseating area`x gives the room it's center of gravity. Upholstered seats face a low table, with enough clear floor around them to keep the gathering space comfortable.", ('seating area', 'The seats gather around a low table, making a small circle for conversation.'))
rule(r'dining|restaurant|resteraunt|diner|cafeteria|banquet', "Tables divide the dining space into separate groups, their surfaces bordered by well-used chairs. A `wcorner table`x sits apart from the central arrangement, offering a more enclosed place to gather.", ('corner table', "Chairs surround a table near the edge of the dining area, away from it's center."))
rule(r'cafe|coffee|doughnut|tea party', TERRAIN[12], ('counter', "The counter faces the cafe seating, it's edge polished by everyday use."), ('tables', 'Small tables provide close-set seats for conversation.'))
rule(r'\bbar\b|tavern|pub|saloon|hookah', TERRAIN[6], ('bar', 'The bar counter offers a long, shared edge where people can gather.'), ('tables', 'Tables stand apart from the counter, with seats facing inward.'))
rule(r'counter|checkout|check.in|prescription|food counter|concession', "A `wcounter`x separates the public standing area from the space behind it. It's durable surface and the wear on the floor in front give this part of the room a clear focus.", ('counter', "The counter has room for people to stand along it's public side."))
rule(r'office|study|chambers|command center', "A `wdesk`x anchors the working area, with a visitor's chair on it's near side. Plain storage and a clear patch of floor keep the office arranged around face-to-face conversation.", ('desk', 'The desk and visitor chair form a compact meeting place within the office.'))
rule(r'meeting|conference|council|senate|court room|audience chamber', "A `wmeeting table`x organizes the formal interior. Chairs face it's center, and the surrounding floor provides room to stand outside the seated group.", ('meeting table', 'Chairs arranged around the table allow the group to face one another.'))
rule(r'foyer|lobby|reception|entry hall|entryway|entrance hall', "The floor opens into a reception space framed by the surrounding walls. A `wwaiting area`x sits along one edge, leaving the center uncluttered for arrivals.", ('waiting area', "Seats along the edge of the room offer somewhere to wait without occupying it's center."))
rule(r'entrance|entry|front walk|back door|cellar door|exit to', "A worn approach defines the threshold of the surrounding space. The ground is clearest in the middle, where repeated passage has left it's mark.")
rule(r'library|bookstore|book store|stacks|shelves|reading|archives|obscure titles', "Rows of books and paper-filled shelving break the room into intimate spaces. A `wreading table`x provides a clear surface among the close-set spines, with the dry smell of paper lingering nearby.", ('reading table', 'The reading table provides shared seating and a clear surface near the shelves.'))
rule(r'classroom|lesson|humanities|supernatural history|latin room|forensics|training and development', "Student desks face a teaching space, with hard flooring visible between the rows. The `wfront row`x sits close to the lesson area, while the back of the room feels less exposed.", ('front row', 'The front row offers seats directly facing the teaching area.'), ('rear desks', 'The rear desks sit behind the other seats, with a view across the classroom.'))
rule(r'laboratory|labratory|\blab\b|experimentation|experiments|diagnostics|quality assurance', "Washable work surfaces divide the laboratory into orderly stations. A `wworkbench`x stands clear of the central floor, with plain walls emphasizing the room's controlled, practical layout.", ('workbench', 'The workbench provides a clear station beside the laboratory floor.'))
rule(r'clinic|hospital|medical|recovery|diagnosis|examination|reparative|radiology|intervention|rehabilitation|wellness|ward', TERRAIN[15], ('waiting chairs', 'A short group of chairs provides a place to wait beside the clinical space.'))
rule(r'cell|prison|dungeon|holding pen|cage', "Hard walls enclose a restricted space. A `wbench`x occupies one edge, leaving a small patch of floor whose worn surface makes the enclosure's limits feel close.", ('bench', "The bench rests against the edge of the enclosure, overlooking it's limited floor space."))
rule(r'chapel|church|cathedral|temple|shrine|ritual', "The room is arranged around a `wplace of observance`x, with open floor before it. Restrained stone and wood surfaces give small movements a noticeable presence in the enclosed space.", ('place of observance', 'The central focus of the chamber has a clear space before it for quiet observance.'))
rule(r'confession', "A close partition divides this small compartment. Worn wood surrounds a narrow `wseat`x, reducing the space to the scale of a private conversation.", ('seat', 'The narrow seat faces the partition within the close wooden compartment.'))
rule(r'theatre|theater|auditorium|amphitheater|concert hall|coliseum', "Rows of `waudience seating`x face the performance area. The clear sightlines and broad interior give the room a sense of expectation even between performances.", ('audience seating', 'The audience seats face the performance space in orderly rows.'))
rule(r'stage|dance floor|dance studio|ballroom|mosh pit|rehearsal', "A broad `wperformance floor`x leaves room for movement. Wear marks it's open surface, and the edges provide space to watch without standing in the center.", ('floor edge', 'The edge of the performance floor offers a place to watch the open area.'))
rule(r'bleachers|dugout|pews|seating|picnic', "Rows of `wseats`x establish a shared vantage point. Worn edges and a narrow standing space give this gathering area a practical, familiar shape.", ('seats', 'The seats gather people into rows, with a little room to stand beside them.'))
rule(r'gym|fitness|weight room|dojo|fencing|arena|dueling|fighting pit|shooting range|archery', "An open `wtraining area`x occupies the center. Repeated use has marked it's surface, while the edges leave room for observers clear of the activity space.", ('sidelines', 'The sidelines offer a place to watch while leaving the central area clear.'))
rule(r'pool', "Water fills a deliberately shaped basin, it's boundary marked by a hard rim. The `wbasin edge`x separates the bathing space from the ground around it.", ('basin edge', 'The hard surface beside the pool provides room to gather at the water\'s edge.'))
rule(r'porch|porche|patio|terrace|veranda|balcony|deck', "An exposed platform forms a small extension of the surrounding structure. Worn boards and hard edges give the `wstanding area`x a simple, open layout.", ('standing area', "The platform leaves a little room to stand together above it's supporting structure."))
rule(r'warehouse|steel mill|shipping|container|loading dock|hangar', TERRAIN[8])
rule(r'workshop|workroom|work area|atelier|artist|painting|kiln|sewing|engineering|design studio', "Work surfaces line the practical interior, leaving room to stand between them. A broad `wworktable`x carries the small scratches and stains of repeated craft work.", ('worktable', 'The worktable provides a shared surface within the working area.'))
rule(r'computer|digital media|recording|music room|photo lab|filming|radio room|dj booth', "Workstations occupy the edges of the room, their cables kept close to the supporting surfaces. The `wseating station`x faces the working area rather than the open floor.", ('seating station', "A seat at the workstation faces it's equipment surface."))
rule(r'laundry|laundromat', "Hard flooring runs between rows of laundry fixtures. A `wfolding counter`x provides a clear surface beside the washing area, where the air holds a trace of detergent.", ('folding counter', 'The folding counter offers a broad surface and room to stand beside it.'))
rule(r'storage|stockroom|storeroom|closet|shed|back room|utility|supply|maintenance', "Plain shelving borders the utility space. Scuffed surfaces and a narrow central standing area reflect the room's role in keeping supplies out of the way.", ('shelves', 'The shelving leaves a narrow place to stand among the storage surfaces.'))
rule(r'basement|cellar|celler', TERRAIN[14])
rule(r'\bshop\b|store|market|bazaar|bizaar|display|department|apparel|clothing|fashion|jewelry|jewelers|jewellery|novelt|accessories|supplies|aisles|pharmacy', TERRAIN[5], ('counter', 'The counter marks the public edge of the sales area.'), ('displays', 'Space between the displays allows a small group to browse together.'))
rule(r'house|home|apartment|cottage|cabana|chalet|residence|lodgings|inn|hotel|motel', TERRAIN[2], ('sitting area', 'A small group of seats occupies one edge of the domestic space.'))
rule(r'\btent\b|teepee|yurt|encampment|camp|lean.to', "A sheltered gathering space lies within a simple camp arrangement. Fabric and rough supporting materials give the enclosure a temporary, close-to-the-ground character.", ('camp center', 'The center of the camp provides room to gather within the surrounding shelter.'))
rule(r'void|nothingness|abyss|no end|dreamheart|rift|between times|dreamscapes|memories|genesis|creation|^age of', "An indistinct expanse surrounds a small point of orientation. Edges seem difficult to hold in view, leaving the `cspace`x with the unsettling intimacy of a half-remembered dream.")
rule(r'bridge|pier|boardwalk|dock|quay', "A hard-wearing span rests above it's supporting structure. Repeated joints divide the surface, and the exposed standing space carries the marks of steady traffic.")
rule(r'\bwell\b(?!-)|fountain', "A `wstone rim`x defines the feature's edge. Wear has smoothed it's upper surface, while the lower stone retains it's rougher grain.", ('stone rim', 'The stone rim provides a place to stand beside the feature.'))
rule(r'plaza|square|courtyard|court|town center|city center|central hub', "An open gathering space spreads across hard, worn ground. The broad center leaves room for groups to stand apart, while the margins provide a more sheltered sense of scale.")
rule(r'elevator|airlock', "Close walls enclose a compact compartment. Metal seams break up the plain surfaces, with only a small standing area between the surrounding panels.")
rule(r'ladder|crane|catwalk', "A rigid metal framework defines this elevated section of the structure. Narrow footing and repeated joints make the exposed construction plainly visible.")
rule(r'boat|aboard|ship|sloop|freighter|ketch|airplane|\bbus\b|\btaxi\b|\btrain\b', "A compact passenger space fits within the craft's structural shell. Close-set surfaces and repeated joints make every part of the interior feel shaped by the demands of travel.")

# Material and layout cues are used only when the room name supplies them.
TRAITS = [
(r'brick', 'Exposed brick shows fine variations in color and worn mortar seams.'),
(r'marble|marbled', 'Pale veins cross the marble surfaces, breaking their polished finish into subtle patterns.'),
(r'wood.panel|oaken|oak accents', 'Wood paneling gives the surrounding surfaces a close, warm grain.'),
(r'tile|tiled', 'Tile joints divide the hard surfaces into a regular pattern.'),
(r'skylight|skylit', 'Glazing overhead breaks the ceiling into framed sections.'),
(r'sunken', 'The recessed central floor gives the room a distinct lower gathering space.'),
(r'cramped|small|tiny|claustrophobic', 'The close proportions leave little spare space between the room\'s edges.'),
(r'large|spacious|expansive|enormous|grand', 'Broad proportions give the central space room to breathe.'),
(r'rundown|run.down|dilapidated|grungy|filthy|squalor|grime|neglected|shabby', 'Grime and worn finishes have settled into the less-used corners.'),
(r'pristine|clean|tidy|renovated', 'Careful upkeep shows in the clean edges and orderly surfaces.'),
(r'graffiti', 'Layered graffiti crowds the exposed surfaces, old marks half-covered by newer ones.'),
(r'glass|glazed', 'Glass panels give the surrounding structure a reflective, layered appearance.'),
(r'fenced|fence', 'A fence establishes a definite boundary along the edge of the space.'),
(r'rock garden', 'Small stones lie arranged among patches of low planting.'),
]

# These signatures distinguish named establishments without claiming that
# adjoining rooms, merchandise transactions, or equipment are accessible.
THEMES = {
"brawling brothers": "Scuffed timber and blunt, sturdy furnishings suit the pub's rough-and-ready character.",
"nymph's rest": "Dark trim and theatrical upholstery give the club a deliberately intimate character.",
"succubus club": "Deep red accents sit against dark finishes, giving the club's interior a close, theatrical feel.",
"starlight lounge": "Small star motifs and dark trim carry the lounge's identity through the interior.",
"house red": "Wine-colored accents and heavy wood give the House Red an old, deliberate formality.",
"pigment and paper": "Paint flecks and paper textures give the studio's carefully used surfaces a handmade character.",
"black rose book": "Dark shelf trim and understated rose motifs lend the bookshop a quiet, slightly somber character.",
"collateral damage": "Utilitarian metal trim and heavy counters give the premises the guarded character of a gun-and-pawn business.",
"moore for less": "Plain shelving and pale finishes reflect the pharmacy's practical emphasis on health supplies.",
"el mercado del mundo": "Different patterns and colors meet in the market's decor, giving it's shared spaces an eclectic character.",
"davedash": "Bright shelf edging and compact displays give the convenience store a brisk, everyday character.",
"studio splendente": "Restrained display spacing and carefully finished trim give the fashion studio a polished appearance.",
"studio luisant": "Fine finishes and restrained decorative details give the studio a composed, fashionable character.",
"fertile valley": "Traces of leaf and stem linger among the florist's work-worn surfaces.",
"rosie's diner": "Chrome edging and familiar diner upholstery give Rosie's a sturdy, unpretentious warmth.",
"oh, for heaven's cake": "Pale bakery colors and neatly finished trim give the cafe a light, carefully presented character.",
"dionysus": "Bottle-shaped motifs and dark shelf trim give the liquor store it's distinctive emphasis.",
"nate's nugs": "Leaf motifs and relaxed furnishings give the premises an informal character.",
"pleasure chest": "Playful packaging colors and discreet display divisions distinguish the adult boutique.",
"unveiled costumes": "Layered fabrics and theatrical details crowd the costume shop's interior.",
"fragrant tree": "The dry scent of incense clings to wood and paper surfaces.",
"knead to relax": "Muted colors and soft finishes lend the treatment premises a restrained calm.",
"the playhouse": "Theatrical red accents and carefully finished wood tie the room to the Playhouse's performance spaces.",
"paine performance": "Hard-wearing finishes and clean lines give the performance complex a practical public character.",
"little nishiki": "Close-grained wood and restrained decorative panels bring a measured rhythm to the restaurant interior.",
"petite cuisine": "Small-scale furnishings and carefully arranged surfaces give the restaurant an intimate character.",
"giovanni": "Warm wood and simple dining-room trim give the Italian restaurant a familiar, welcoming character.",
"haven hardware": "Heavy-duty shelving and scuffed industrial finishes suit the hardware store's practical purpose.",
"hook, line": "Fishing motifs and durable fittings connect the shop to Haven's coastal life.",
"hunt & hook": "Outdoor-trade displays and durable surfaces give the store a practical character.",
"savage talent": "Acoustic finishes and performance imagery give the premises a working entertainment-studio character.",
"white oak": "Pale institutional finishes and orderly spacing give White Oak's interior it's controlled, formal character.",
"mandala": "Fine geometric motifs sit among carefully spaced jewelry displays.",
"old world jewel": "Small display settings and traditional wood trim lend the jeweler's interior an old-fashioned precision.",
"stellar": "Crisp display lines and contrasting finishes give the fashion premises a carefully arranged appearance.",
"hometown diner": "Durable tables and nostalgic trim give the dining premises the comfortable wear of a local gathering place.",
"loving kitchen": "Plain, well-kept furnishings make the shared interior feel practical and welcoming.",
"beelzebubbles": "Scuffed machine surrounds and irreverent decoration give the laundromat a scrappy character.",
"howl at the moon": "Gothic trim and dark wood lend the gathering space a deliberately nocturnal style.",
"cafe salerno": "Warm finishes and close-set furnishings give the cafe a compact neighborhood character.",
"the retreat": "Game and costume motifs lend the Retreat's interior a playful, informal identity.",
"museum": "Carefully separated display areas and restrained finishes give the museum a measured, contemplative character.",
"aboard": "Ribbed bulkheads and inset panels give the shipboard compartment it's distinctive structural rhythm.",
"castle hearts": "Heart motifs and exaggerated proportions give the castle's setting a storybook strangeness.",
"new hope": "Orderly, austere finishes give the civic settlement a deliberately regimented character.",
}

EXACT = {}
def exact(name, prose, *places):
    EXACT[name.casefold()] = (prose, list(places))

exact('The World Storehouse', 'Broad storage bays recede across a plain floor, their unadorned surfaces giving this repository a scale beyond any ordinary shop. The `wcentral standing area`x is kept clear among the bays.', ('central standing area', 'A clear area lies between the storage bays, with room to gather.'))
exact('The Dreamheart', 'The surrounding dream draws inward toward a `cpale, wavering center`x. Shapes lose their edges as they approach it, leaving the impression of a place assembled from beginnings rather than walls.')
exact('Yggdrasil', 'An immense `gtrunk`x rises from roots broad enough to divide the ground into valleys. Bark folds into deep ridges, and the vast branching structure gives this dream of the World Tree an almost architectural scale.')
exact('the steel mill', 'Heavy steel framing spans broad industrial floors. Repeated supports and worn concrete divide the mill into immense working bays, with rust collecting at joints and handling scars crossing the open ground.')
exact('the White Oak Biodome', 'Curving structural ribs divide the biodome enclosure above cultivated ground. Beds of vegetation occupy the space within the framework, their irregular leaves set against the deliberate geometry of the `wdomed shell`x.')
exact('White Oak Biodome', EXACT['the white oak biodome'][0])
exact('Moore Woods', 'Closely spaced `gtrees`x rise from Moore Woods\' uneven floor. Old leaves settle around exposed roots and fallen limbs, breaking the ground into small pockets beneath the tangled branches.')
exact("Warden's Wood", 'Old trunks stand close together in `gWarden\'s Wood`x, their roots ridging a deep litter of leaves. The compressed spaces between them give the woodland an enclosed, watchful character.')
exact('Deadwood', 'Weathered limbs and standing trunks crowd the ground in `wDeadwood`x. Pale splinters interrupt the dark leaf litter, and the woodland feels layered with the remnants of older growth.')
exact('Blackmoon Woods', 'Dark bark and dense undergrowth give `gBlackmoon Woods`x a close-grained texture. Tangled roots break the ground into uneven steps, while branches overlap tightly above them.')
exact('Arkwright Cemetery', "Weathered `wheadstones`x stand in measured rows across Arkwright Cemetery. Older stonework has softened at it's edges, and grass gathers around the bases of markers whose spacing gives the ground it's solemn order.")
exact('the Arkwright Mausoleum', 'Heavy stone walls enclose the mausoleum, their joints precise beneath the wear of age. Recessed memorial surfaces face a small `wcentral space`x, where the weight of the surrounding masonry feels especially close.', ('central space', 'A small clear area lies before the memorial stonework.'))
exact('Haven Bay', 'The waters of `cHaven Bay`x occupy a broad coastal basin. Surface patterns overlap across the open reach, concealing the submerged contours beneath them.')
exact('Willow Cove', "A sheltered curve of `ysand`x gives Willow Cove it's intimate scale. Shell fragments and fine grains settle into shallow ridges across the yielding ground.")
exact('Sidney Beach', 'Broad stretches of `ysand`x form Sidney Beach, with compressed patches where feet have passed and looser grains gathered along their edges. The open beach offers little enclosure.')
exact('Underlook Beach', 'Coarse `ysand`x mixes with scattered pebbles across Underlook Beach. The uneven texture gives the shore a rougher character, with small hollows collecting the finer grains.')
exact('Badwater Park', "Worn patches interrupt the `ggrass`x of Badwater Park. The open ground has the practical, imperfect feel of a neighborhood green, with rougher growth at it's margins.")
exact("Rosie's Diner", 'Chrome edging frames a long `wcounter`x at Rosie\'s, while upholstered `wbooths`x divide the dining floor into familiar little alcoves. The hard flooring is worn between them, and the room carries the faint, settled scent of coffee.', ('counter', 'Stools face the chrome-edged counter in a sociable line.'), ('booths', 'Upholstered benches face across a diner table, forming a close little conversation space.'))
exact('the mayor\'s office', 'A broad `wdesk`x faces the visitor space in this formal civic office. Restrained wood trim and carefully aligned chairs give the room an air of deliberation, while the clear floor keeps attention on whoever occupies the desk.', ('desk', "Visitor chairs face the mayor's desk across it's broad working surface."))
exact('the planetarium', 'Curved surfaces gather above `wviewing seats`x arranged around the dome\'s center. The room\'s geometry directs attention overhead, with the seated area kept clear of decorative clutter.', ('viewing seats', 'The seats face into the planetarium\'s shared overhead viewing space.'))
exact('the Bowling Lanes of The Alley', 'Long polished lane surfaces dominate this part of The Alley, their parallel edges drawing the eye across the room. The `wseating area`x sits behind the approaches, separated from the lanes by their change in flooring.', ('seating area', 'Seats stand behind the lane approaches, giving groups room to gather clear of the polished lanes.'))
exact('the Arcade Hall of The Alley', 'Rows of arcade cabinets create short aisles in The Alley\'s game hall. Scuffed cabinet edges and bold decorative panels crowd the walls around a `wcentral aisle`x.', ('central aisle', 'The aisle offers room to gather between the cabinet rows.'))
exact('the Beelzebubbles Laundromat', 'Rows of round-fronted laundry machines face a scuffed central floor. Irreverent decoration crowds the walls, while a long `wfolding counter`x supplies a practical pause in Beelzebubbles\' visual clutter.', ('folding counter', 'The long counter provides room to fold laundry or stand beside someone doing so.'))
exact('the lighthouse stairs', 'Treads follow the lighthouse\'s close, curving wall. Worn edges record countless climbs, and the enclosing masonry gives the stair a tight, vertical rhythm.')
exact('the beacon', "The lighthouse's optical assembly dominates the chamber, glass and metal arranged around the `wcentral housing`x. The cramped surrounding space emphasizes the apparatus' scale without obscuring it's carefully fitted structure.", ('central housing', 'A narrow standing space borders the beacon housing.'))
exact('the old gallows', "A weathered timber frame rises above a scarred platform. It's blunt construction leaves the purpose of the `wgallows`x starkly apparent, with grain and age cracks visible in the exposed wood.")
exact('the waters of life', "The `cwater`x has an unusual clarity, giving it's layered depths a glasslike appearance. The surrounding expanse feels composed and still in it's proportions, without a solid surface on which to stand.")
exact('the center of Rhagost', 'Heavy, time-worn surfaces gather around Rhagost\'s central space. The scale feels built for a settlement larger than the immediate gathering area, with the `wopen center`x giving the surrounding mass a point of reference.')
exact('the Mobious path', 'The `wpath`x holds a disturbingly repetitive shape. Worn ground and enclosing surfaces recur with an almost remembered familiarity, making the immediate stretch easy to see and difficult to place.')
exact('the Goblin Market\'s Library', 'Uneven ranks of books crowd the Goblin Market\'s library. Bindings of mismatched size and texture press against dark shelving, while a `wreading table`x provides a small island of order among them.', ('reading table', 'The table provides a shared surface between the irregular ranks of books.'))
exact('the Fleshforming Clinic', 'Smooth treatment surfaces sit within an otherwise rough-built enclosure. The contrast between the clean `wconsultation area`x and the surrounding market architecture gives the clinic an unsettling precision.', ('consultation area', 'Seats face a plain treatment surface within the clinic.'))
exact('Arcane Dueling Circle', 'Circular markings define the `wdueling ground`x. Scuffs cross their edges, but the central space remains open, with the circle edge giving observers a clear sense of the arena\'s shape.', ('circle edge', "The edge of the marked circle offers a place to gather clear of it's center."))
exact('the Alchemical Labratory', 'Work surfaces crowded with fixed racks border a clear central floor. Marks of spills and careful cleaning overlap across the `wworkbench`x, giving the alchemical laboratory a history of exacting, imperfect work.', ('workbench', 'The workbench offers a clear standing station among the fixed racks.'))
exact('the Magical Workshop', 'Inscribed working surfaces occupy the workshop\'s edges, their patterns interrupted by ordinary scratches. A `wworktable`x stands in the center, bringing arcane craft down to the scale of patient handwork.', ('worktable', 'The central table provides a shared working surface.'))
exact('the Engineering Workshop', 'Metal brackets and measured work surfaces give the workshop a rigid geometry. Filing marks and handling scars surround a sturdy `wworkbench`x, where the room\'s practical layout comes together.', ('workbench', 'The bench leaves room for several people to examine work together.'))
exact('the Folly', 'Mismatched woodwork and carefully patched furnishings give the Folly the character of a refuge assembled over time. A `wseating nook`x sits against the irregular wall, close enough for low conversation.', ('seating nook', 'The nook gathers several seats around a patched wooden table.'))
exact('the Court room', 'The room\'s formal arrangement faces the raised judicial area. `wPublic benches`x stand in orderly rows, with clear floor separating the observers from the focus of proceedings.', ('public benches', 'Rows of benches face the judicial area across the open floor.'))
exact('the crematorium', 'Heat-marked masonry surrounds heavy metal furnace housings. The plain `wstanding area`x is kept clear, giving the room a severe order and an unmistakably final purpose.', ('standing area', 'A clear space lies before the furnace housings.'))
exact('a room full of body drawers', 'Banks of metal-fronted compartments occupy the walls. Their repeated seams and small handles lend the morgue a stark regularity, leaving a narrow `wcentral aisle`x between them.', ('central aisle', 'The aisle lies between the banks of mortuary compartments.'))
exact('a room full of clocks', 'Clock faces crowd the surrounding walls, their differing sizes breaking the room into circles and narrow intervals. The `wcentral floor`x feels small within this accumulation of measured time.', ('central floor', 'A clear patch of floor lies within the surrounding ranks of clocks.'))
exact('the White Oak Biodome airlock', 'Close metal panels enclose a compact transition chamber. Hard seals and repeated structural seams distinguish the airlock from the planted environment it serves.')
exact('the Haven History Museum - Prehistoric Haven', 'Earth-toned display panels and stone-textured mounts organize this gallery around Haven\'s distant past. The `wviewing area`x leaves room to pause before the exhibits without crowding their edges.', ('viewing area', 'The gallery floor provides room to examine the prehistoric displays.'))
exact('the Haven History Museum - The Duncan Foundation', 'Formal display groupings present the Duncan Foundation within a restrained gallery. The `wviewing area`x is arranged for close attention to the exhibit panels and their careful sequence.', ('viewing area', 'The clear gallery floor faces the Foundation displays.'))
exact('the Haven Historical Museum - Maritime Trade & Commerce', 'Maritime display motifs and carefully separated exhibits trace the town\'s relationship with shipping. The `wviewing area`x allows the gallery\'s rope, wood, and hull-shaped details to be taken in at a measured pace.', ('viewing area', 'There is room to stand together before the maritime exhibits.'))
exact('the Haven Historical Museum - The Founding of Haven', 'A sequence of historical panels gives this gallery a deliberate narrative shape. The `wviewing area`x faces displays devoted to Haven\'s beginnings, with restrained finishes keeping attention on the material presented.', ('viewing area', 'The gallery floor faces the founding exhibits.'))
exact('the Haven History Museum - Modern Day Haven', 'Contemporary display panels organize the gallery around the town\'s more recent identity. Clean edges frame the exhibits, with a `wviewing area`x allowing visitors to pause over the details.', ('viewing area', 'The open gallery floor provides room to examine the modern-history displays.'))
exact('the Haven History Museum - The Aquarium', "Thick viewing panels separate the gallery from it's water-filled displays. Their layered reflections give the room an unusual depth, with a `wviewing area`x set back from the glass.", ('viewing area', 'The standing space faces the aquarium glazing.'))

# Additional functions used by the civic, agricultural, dream, and travel maps.
rule(r'\b(?:park|farmland|green|valley|hills|hill|crop|cornfield|potato|tomato|carrot)\b', "Low growth covers the worked and open ground. Soil shows between the plants, with the uneven texture of stems and leaves defining it's surface.")
rule(r'\b(?:lot|rubble|ruins|remains|ruined|burnt|shattered)\b', "Broken material lies across rough, exposed ground. Fragmented edges and worn foundations give the site an irregular layout, with small pieces gathered in it's lower pockets.")
rule(r'\b(?:stables?|barn|hen house|pig pen|chicken run|row of stalls|grain silo)\b', "Hard-wearing agricultural materials enclose the farm space. Timber, packed ground, and traces of straw give it's practical layout a close connection to the surrounding husbandry.")
rule(r'channel', "A recessed watercourse occupies the center of the space. Worn stone borders it's length, with sediment gathered against the lower seams of the channel.")
rule(r'dumpster|dumpsters', 'Heavy refuse containers occupy a rough service space. Scuffed metal and stained ground give the area an unmistakably utilitarian character.')
rule(r'fence|railing', 'A repeated line of uprights marks the boundary here. Weathering has roughened the exposed surfaces, while the standing space beside them remains narrow and plainly defined.')
rule(r'baseball|first base|second base|third base|home base|foul line|pitcher|short stop|dash (?:to|home)|athletics|sport facilities|basketball|volleyball|skating|ice rink', "The playing surface spreads across an open area, it's boundaries established by the geometry of the sporting ground. Wear concentrates where movement repeatedly crosses the surface.", ('sidelines', 'The sidelines provide a place to gather clear of the main playing space.'))
rule(r'\b(?:massage|spa|beauty|treatment)\b', "Soft finishes surround a carefully arranged treatment space. A `wresting seat`x stands near it's edge, with the clear floor lending the room a deliberate calm.", ('resting seat', 'The seat offers a quiet place beside the treatment space.'))
rule(r'\b(?:art room|colour palette|smash room|repair|workplace)\b', "Marked work surfaces border a practical interior. A `wworktable`x gathers the room's activity into a shared space, it's surface showing the traces of repeated use.", ('worktable', 'The table provides a shared working surface.'))
rule(r'book nook|children.s corner|comics section|librarian.s desk', 'Shelving and close-set furnishings bring this reading space down to an intimate scale. A `wreading seat`x offers a place to settle among the paper-filled surroundings.', ('reading seat', 'The seat rests near the shelving, with room for quiet company.'))
rule(r'arcade|pool tables|jungle gym|winding tubes|tube slide|playground', 'The recreation structures divide the space into distinct activity areas. Their worn surfaces and repeated curves give the room a playful but well-used character.', ('gathering area', 'A clear gathering area lies beside the recreation structures.'))
rule(r'\b(?:breakroom|break room|community room|leisure hub|vip|v\.i\.p|private area|brothel|bordello|club|the dive|lodge)\b', 'A `wseating area`x occupies the gathering space, with chairs facing inward around a low table. The surrounding finishes give the room a close, conversational scale.', ('seating area', 'The inward-facing seats provide a place for a small group to gather.'))
rule(r'\b(?:hall|halls|passage|second floor|third floor|mezzanine|antechamber|east end|west end|wing|wings)\b', 'An open strip of flooring lies between the surrounding structural surfaces. Worn patches show where people pass, while the margins provide a quieter place to pause.')
rule(r'\b(?:tower|clocktower|clock face|clock face|beacon|spire|spires)\b', "Heavy structural surfaces define the tower space. It's close vertical proportions give the surrounding stone and framework a sense of height beyond the immediate standing area.")
rule(r'\b(?:attic|loft)\b', 'The upper framework of the building shapes this tucked-away space. Close roof supports and a plain floor give the interior a compact, elevated character.')
rule(r'mausoleum|morgue|dead|grave', 'Heavy surfaces enclose a solemn space devoted to the dead. The clear central floor emphasizes the weight and stillness of the surrounding memorial structure.')
rule(r'security|interrogation|interview|detective bureau|observation|reprogramming', "A `wtable`x occupies a sparse institutional room. Plain chairs face across it's surface, with an uncluttered floor leaving little to draw attention away from the people present.", ('table', 'Chairs face one another across a plain table.'))
rule(r'gas station|gas pumps|drive.through|driveway|off.ramp', "Hard paving supports a practical vehicle area. Tire wear interrupts it's surface, and the margins carry the scuffs and grit of repeated traffic.")
rule(r'airport|port|depot|station|terminal', 'Broad circulation space and durable structural surfaces give this transport area a practical scale. A `wwaiting area`x occupies one edge, leaving the central ground clear.', ('waiting area', 'The waiting area provides room to gather beside the main circulation space.'))
rule(r'gazebo|gazeebo|pavilion|overlook|beacon point', "A defined observation space stands amid exposed structural surfaces. It's open proportions lend the standing area a sense of separation from the ground immediately around it.")
rule(r'\b(?:maze|labyrinth)\b', 'Close boundaries divide the ground into a repeating sequence of small spaces. Similar textures recur along the edges, making the immediate section of the maze easier to recognize than to place.')
rule(r'\b(?:mine|mines|sublevels|hole|pit)\b', 'Rough-cut surfaces close around the excavated space. Loose fragments gather along the floor, and exposed seams show the irregular structure of the surrounding ground.')
rule(r'\b(?:room|chamber|chambers|suite|suites|trailer|cabin|appartment|estate|hideout|hideaway|lair|alcove)\b', 'The enclosed space has a plain floor and close surrounding surfaces. A clear central area leaves room to stand together, with the quieter margins set back from the middle.')
rule(r'fire pit|firepit|bonfire', "A ring of heat-marked material surrounds the fire site. Ash and blackened fragments settle into it's center; the surrounding `wgathering area`x lies clear of the scorched ground.", ('gathering area', "The gathering area borders the fire site, clear of it's ash-darkened center."))
rule(r'butcher|curing|meat|seafood|produce|bakery|grocery|snacks|cold drinks|sundries|lingerie|attire|firearms|defence|defense|cosmetics|hygiene|live bait', 'Ordered displays and hard-wearing surfaces divide the retail space. A `wdisplay aisle`x gives browsers room to stand together without crowding the edges.', ('display aisle', 'The aisle provides a clear standing space among the displays.'))
rule(r'bank|vault', 'Heavy finishes and deliberately open floor space give the financial premises a restrained, guarded character. The `wpublic standing area`x sits clear of the surrounding fittings.', ('public standing area', 'The clear standing area provides room for people to wait together.'))
rule(r'city|district|downtown|sprawl|neighborhood|neighbourhood|territory', 'Built surfaces and open ground divide the settlement into a patchwork of human-scale spaces. Wear gathers along the most-used ground, lending the surroundings a settled texture.')
rule(r'mist|fog|portal|godrealm|the other|the wilds|^hell$', "The surrounding space has an uncertain depth. It's textures seem to recede just beyond easy recognition, giving the immediate ground the uneasy clarity of a remembered dream.")
rule(r'castle|palace|keep|throne', 'Massive walls and formal proportions lend the chamber a weighty, ceremonial character. The `wcentral floor`x lies clear within the surrounding structure.', ('central floor', 'A broad clear floor provides room to gather within the formal surroundings.'))
rule(r'\b(?:street|road|way|run)\b', TERRAIN[1])

exact('The Haven History Museum - Possible food place?', 'Plain walls enclose a spare room in the museum. The open floor and unadorned surfaces give it the restrained character of an unused gallery annex; no exhibits or dining fittings occupy the space.')
exact('The Haven History Museum - Extra Space', "A spare gallery space lies within the museum's structure. The uncluttered floor and plain display walls make the room feel quiet and spacious, with no exhibits occupying it's center.")
exact('the dismal Devilwood McDonald\'s', 'Bright corporate colors sit uneasily against scuffed flooring and worn plastic trim. A `wservice counter`x faces the dining space, where `wbooths`x form compact alcoves along the edge of the room.', ('service counter', "The counter offers room to stand along it's customer side."), ('booths', 'Plastic-trimmed booths provide close-set seats around fixed tables.'))
exact("'Lucky Garden #3' at The Strip", 'Compact tables and simple decorative panels give Lucky Garden #3 a practical dining layout. A `wcorner table`x sits against the wall, with clear floor between the dining groups.', ('corner table', 'The corner table provides a close gathering space at the edge of the restaurant.'))
exact("'The Glaze' at The Strip", "A glazed `wdisplay counter`x gives the small bakery it's focus. Pale surfaces and compact furnishings frame a `wseating nook`x set back from the shop's central floor.", ('display counter', 'The counter faces the clear customer space.'), ('seating nook', 'The nook provides a small place to sit beside the bakery floor.'))
exact("'Close Knit Duds' at The Strip", 'Folded textiles and hanging displays give Close Knit Duds a soft, layered texture. A `wbrowsing aisle`x runs between the clothing displays, with room to stop beside their edges.', ('browsing aisle', 'The aisle provides room to browse together among the textile displays.'))
exact("'Five and Under' at The Strip", 'Compact displays gather everyday small goods into close-set rows. The store\'s bright, economical fittings face a scuffed `wcustomer aisle`x.', ('customer aisle', 'The aisle provides a clear place to stand among the displays.'))
exact("'Risque & Rebellious' at The Strip", 'Contrasting fabrics and bold display forms give the boutique a theatrical edge. A `wbrowsing area`x lies between the clothing arrangements, where layered textures crowd the eye.', ('browsing area', 'The display floor provides room to browse together.'))
exact('Collateral Damage - Lyceum of the Mists', 'A `wstudy table`x forms the center of this quieter part of Collateral Damage. Close shelving and restrained arcane motifs set the room apart from the premises\' utilitarian retail spaces.', ('study table', 'The table offers shared seating within the study area.'))
exact('Collateral Damage - Victorious Secret', 'Carefully separated displays present this department with unusual discretion. Heavy trim connects it to Collateral Damage, while the `wconsultation area`x provides a less exposed place to pause.', ('consultation area', 'A small seating arrangement stands beside the displays.'))
exact('the Owl\'s Post', "Small compartments and paper-handling surfaces organize the postal interior. A `wsorting counter`x provides it's central working edge, with clear floor in front for arrivals.", ('sorting counter', 'The counter provides room to stand beside the paper-sorting area.'))
exact('the printing press', "Heavy metal framing surrounds the press assembly. Rollers, plates, and fixed housings form a dense mechanical shape beside a clear `wworking area`x, with traces of ink settled into it's older seams.", ('working area', "The clear space beside the press gives people room to examine it's exterior."))
exact('the grain silo', 'Curving storage walls rise around a confined central space. Fine grain dust settles into the seams, emphasizing the tall, enclosed shape of the agricultural structure.')
exact('the pig pen', "Low agricultural boundaries enclose packed, churned ground. Straw fragments and worn timber give the pen a rough texture, with it's center more heavily disturbed than it's edges.")
exact('a chicken run', "A simple enclosure surrounds scratched earth. Small depressions and scattered straw interrupt the ground, with the boundary giving the chicken run it's close, practical shape.")
exact('the horse stable', 'Timber partitions divide the stable into stalls beside a practical central aisle. Straw and the grain of worn wood give the enclosure a warm, earthy texture; the `waisle`x leaves space to gather clear of the stall edges.', ('aisle', 'The aisle provides room to stand within the timber-framed stable.'))
exact('the tomato stakes', 'Rows of slender stakes rise from worked soil. Tied stems and rough leaves gather around their supports, giving the crop a repeated vertical pattern amid the lower ground.')
exact('the cornfield', 'Rows of sturdy corn stalks divide the worked ground. Long leaves overlap into close screens, with exposed soil forming narrow intervals between the planted rows.')
exact('the carrot crop', 'Fine, divided carrot foliage spreads low over worked earth. The planted rows remain visible as repeated bands of green above the darker soil.')
exact('the potato patch', 'Low, leafy potato plants gather over mounded soil. Uneven ridges divide the cultivated patch, with loose earth showing between the thickening leaves.')
exact('the airlock of the White Oak biodome', EXACT['the white oak biodome airlock'][0])
exact('the rooftop of a double-wide trailer', 'Seamed roofing panels form the narrow upper span of the trailer. The exposed surface follows the simple rectangle of the home below, with patches and weathered joints interrupting the metal.')
exact('The Void', 'An unbounded `cvoid`x surrounds a single point of awareness. There is no wall or floor to measure it against, only the strange impression that the emptiness is close enough to touch.')
exact('Creation', "A pale, undefined space gathers around a clear center. It's edges remain soft and unresolved, giving this place of beginnings the `cquiet expectancy`x of a form not yet chosen.")
exact('Time-Out', "Plain walls and an uncluttered floor enclose a small, quiet room. It's empty center and restrained surfaces give the space an air of deliberate separation from the activity beyond it.")
exact('Movement and Helpfiles', 'Simple teaching panels border an open practice floor. The room\'s uncluttered proportions leave space to become familiar with movement, while a `wreading area`x offers a quiet place beside the instructional displays.', ('reading area', 'The reading area faces the instructional panels.'))

from room_landmarks import install
install(exact, rule, TERRAIN)
from room_interiors import install as install_interiors
install_interiors(exact)
