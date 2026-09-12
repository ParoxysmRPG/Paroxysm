"""Editorial building blocks for distinct saved interiors.

Each scene supplies a focal detail, a second physical detail, and an atmosphere.
These are composed when authoring the saved catalogue, never during play.
No scene establishes weather, occupants, a working service, or an extra exit.
"""

# Surface words describe finishes, not automatically usable game objects.
SURFACES = {
    'domestic': ['honey-colored wood', 'smoke-blue paint', 'cream plaster', 'dark walnut', 'muted green paint', 'chalk-white wood', 'warm terracotta', 'pearl-gray paint'],
    'institution': ['pale green paint', 'cream enamel', 'gray tile', 'brushed steel', 'blue-gray paint', 'white ceramic', 'dark wood', 'sand-colored plaster'],
    'industrial': ['ribbed steel', 'red oxide paint', 'dark iron', 'poured concrete', 'galvanized metal', 'yellow safety paint', 'blackened brick', 'copper-colored rust'],
    'stone': ['slate-gray stone', 'pale limestone', 'dark basalt', 'rust-colored sandstone', 'cream mineral deposits', 'green-veined rock', 'chalky stone', 'blue-gray shale'],
    'earth': ['pale grit', 'dark leaf mold', 'rust-colored earth', 'fine gravel', 'weathered bark', 'silver-gray roots', 'green moss', 'chalky dust'],
}

# A meaningful focal feature changes along with the secondary detail. Material
# and position provide additional local specificity, never a numeric room tag.
SCENES = {}
def scene(kind, family, focus, detail, atmosphere):
    SCENES[kind] = {'family':family, 'focus':focus, 'detail':detail, 'atmosphere':atmosphere}

scene('bare','domestic',[
    'A shallow recess interrupts the {side} wall, outlined by a narrow lip of {surface}.',
    'A strip of {surface} stops short of the {side} corner, exposing the construction beneath the finish.',
    'Two broad planes meet at an awkward angle on the {side} side, with {surface} picked out along the join.',
    'A square patch of {surface} marks the {side} wall where the surrounding finish changes depth.',
    'Near the {side} wall, the floor rises into a low ridge edged with {surface}.',
    'The {side} end narrows around a broad structural pier faced in {surface}.',
],[
    'The floor carries a faint rectangular outline, clearer at one end than the other.',
    'Fine tool strokes remain visible beneath the last layer of wall finish.',
    'Small pinholes form an uneven line just above the height of a raised hand.',
    'A hairline seam crosses the floor and disappears beneath the base of the wall.',
    'The ceiling has a shallow step that makes one corner seem unexpectedly close.',
    'An old repair has dried to a slightly different shade, revealing the shape of the patch.',
    'The lower edges are rounded where an otherwise sharp finish meets the floor.',
    'A narrow shadow lies inside the deepest joint, emphasizing the spare geometry.',
],[
    'Without furniture to soften the enclosure, every small sound acquires a dry little echo.',
    'The undecorated surfaces leave the proportions unusually easy to read, from the low corners to the open middle.',
    'There is a faint mineral smell beneath the dry air, the scent of a room reduced to the materials that make it.',
    'The open floor makes the slightest unevenness conspicuous, a landscape of small seams and shallow shadows.',
    'The quiet has an unfinished quality, as though the next ordinary use might finally give the space a character.',
])

scene('bedroom','domestic',[
    'A {bed} sits against the {side} wall beneath a broad headboard framed in {surface}.',
    'A narrow band of {surface} follows the {side} wall behind the {bed}, giving the sleeping corner a quiet emphasis.',
    'The {bed} lies off-center toward the {side} side, balanced by a shallow wall recess finished in {surface}.',
    'Rectangular panels of {surface} make a calm pattern behind the {bed} at the {side} end.',
    'The {side} corner holds a {bed} with rounded edges, the nearby trim picking up the tones of {surface}.',
    'Above the {bed}, a low section of the {side} ceiling meets a broad strip of {surface}.',
],[
    'The coverlet is folded back in a wide band, exposing a lighter lining and a row of small stitches.',
    'Two differently textured pillows soften the head of the mattress; the nearer one keeps a shallow crease.',
    'A small fabric wall hanging has an uneven lower edge, with a single thread curling away from the weave.',
    'A framed botanical print makes the room feel personal without explaining who chose it.',
    'The bedding has a narrow stitched border that repeats in the cloth covering a small bedside surface.',
    'A plain rug ends just short of the sleeping furniture, leaving a crescent of bare floor beside the mattress.',
    'A folded blanket adds a deeper patch of color near the foot, the wool visibly coarser than the sheets.',
    'Fine vertical grain runs through the nearest wooden fitting, interrupted by one pale, oval knot.',
],[
    'Fabric takes the hard edge off sound, leaving the sleeping corner close enough for a lowered voice.',
    'The room smells faintly of aired bedding, with a drier trace of wood beneath it.',
    'The arrangement makes rest feel private without shutting company out of the small space beside the bed.',
    'There is little here that demands attention; the small textures become more noticeable the longer anyone stays.',
    'The quiet is domestic and modest, shaped by the distance between an elbow, a pillow, and a familiar wall.',
])

scene('living','domestic',[
    'A {sofa} faces inward from the {side} wall, beneath a shallow decorative band of {surface}.',
    'The {side} corner gathers a {sofa} and a low, oval table against a finish of {surface}.',
    'A broad section of {surface} frames the {sofa} at the {side} end, giving the room a comfortable center.',
    'The {sofa} sits at a slight angle to the {side} wall, breaking up the straight lines of the {surface} trim.',
    'A shallow recess faced in {surface} shelters the {sofa} on the {side} side.',
    'The {side} half is arranged around a {sofa}, with {surface} outlining the quieter edges of the room.',
],[
    'A woven throw lies in a broad fold over one arm, the fringe slightly longer on one side.',
    'A low table has softly rounded corners and a pale inlay that follows the outer edge.',
    'Small framed prints hang at different heights, making an informal balance out of their mismatched proportions.',
    'A rug carries a repeating diamond pattern, interrupted near one edge by a deliberately contrasting border.',
    'A shallow decorative bowl catches the room in a curved, imperfect reflection.',
    'The upholstery changes texture where a smooth outer panel meets the heavier weave of the cushions.',
    'A little shelf holds an arrangement of ordinary ornaments chosen for color rather than symmetry.',
    'The floor has a softer finish around the seats, with a clearer strip left for crossing the room.',
],[
    'The seats turn attention toward company, leaving the surrounding details to be noticed between exchanges.',
    'Fabric and furniture polish mingle faintly in the enclosed air, a comfortable smell without much ceremony.',
    'The room feels intended for the part of a visit after everyone has stopped deciding where to stand.',
    'Small sounds lose their sharpness among the soft furnishings, giving a conversation room to slow down.',
    'There is an easy domestic scale here: nothing grander than a shared table edge and a place to settle.',
])

scene('bathroom','institution',[
    'A narrow border of {surface} frames the {washing} along the {side} wall.',
    'The {washing} is recessed beneath a shallow lintel faced in {surface} at the {side} end.',
    'A vertical strip of {surface} divides the {washing} from the room\'s closer fittings on the {side} side.',
    'The {washing} occupies the {side} corner, where a change in {surface} makes the drain line easy to see.',
    'A broad panel of {surface} backs the {washing}, with the remaining fittings held close to the {side} wall.',
    'At the {side} end, the {washing} sits within a squared recess picked out in {surface}.',
],[
    'The mirror has a narrow beveled edge, splitting nearby shapes into a second, thinner reflection.',
    'Fine mineral traces gather beneath the fittings, paling toward the places that dry most quickly.',
    'A small ceramic soap dish has a ridged bottom and one darker line along the glaze.',
    'Drainage grooves turn at a careful right angle before disappearing beneath the nearest fixture.',
    'The taps have rounded shoulders that show every small distortion in their reflective finish.',
    'A recessed shelf keeps washing things close to hand without protruding into the narrow floor.',
    'The hard floor is divided into small squares, with wider joints marking the boundary of the wet surface.',
    'A pale towel folded over a simple rail adds the only soft texture among the washable surfaces.',
],[
    'A clean soap scent lingers in the damp air, and the hard enclosure gives each movement a crisp edge.',
    'The close fittings leave the room practical and intimate, scaled to the small business of washing.',
    'Reflections repeat between the polished surfaces, making the modest enclosure seem more intricate than it is.',
    'The air carries a faint mineral coolness beneath the sharper smell of cleaning.',
    'Nothing is far from reach; the room works through compact arrangements rather than spare space.',
])

scene('office','institution',[
    'The {desk} faces the {side} half of the room beneath a restrained band of {surface}.',
    'A shallow alcove of {surface} backs the {desk} at the {side} end.',
    'The {desk} stands diagonally to the {side} wall, making an otherwise square office feel less formal.',
    'A broad panel of {surface} frames the working side of the {desk} along the {side} wall.',
    'The {side} corner holds a compact {desk}, with a clear gap left between the working surface and the visitor\'s chair.',
    'The {desk} sits beneath a low section of ceiling on the {side} side, where {surface} emphasizes the room\'s structure.',
],[
    'A document tray has been turned slightly away from the visitor, presenting the neat backs of stacked folders.',
    'A framed diagram uses hairline rules and small labels, rewarding a closer look without dominating the office.',
    'The chair backs have narrow horizontal slats that echo the divisions of the storage behind them.',
    'A small blotter marks a precise rectangle on the working surface, leaving a broad margin around it.',
    'A line of shallow drawers breaks the lower fittings into compact, carefully measured compartments.',
    'A plain clock face sits among the wall fittings, modest enough to become conspicuous only during a pause.',
    'The edge of a pinned paper curls forward from an otherwise tightly ordered notice panel.',
    'A narrow strip of cork makes a warmer patch among the harder office surfaces.',
],[
    'The arrangement sets a clear distance between host and visitor, close enough for courtesy to carry some weight.',
    'Paper and dry furniture polish give the room the settled smell of work that mostly happens sitting down.',
    'The ordinary objects make the office feel occupied by a routine even when nobody is carrying it out.',
    'There is room for a conversation to become private without the room itself becoming comfortable.',
    'The cleared working edge gives every meeting the same quiet starting point.',
])

scene('kitchen','domestic',[
    'The {prep counter} follows the {side} wall beneath a narrow splashback of {surface}.',
    'A squared return in the {prep counter} makes a compact working corner on the {side} side.',
    'A band of {surface} separates the {prep counter} from shallow storage along the {side} wall.',
    'The {side} end is organized around a broad {prep counter}, with the heavier fittings set close beneath it.',
    'The {prep counter} narrows beside a structural pier faced in {surface} at the {side} end.',
    'A deep working recess on the {side} side contains the {prep counter} and a neat strip of {surface}.',
],[
    'A row of hooks follows the underside of a shelf, each casting a small curved shadow against the backing.',
    'The cabinet fronts use inset panels, their fine borders making a quiet pattern around the practical fittings.',
    'A draining surface slopes through a series of shallow ridges toward the washing recess.',
    'A broad chopping board has a pale border around the darker grain of the center.',
    'A narrow spice shelf gives the room a line of small, repeated shapes at eye level.',
    'A tiled strip changes direction at the corner, where the pattern has been carefully cut to fit.',
    'The lower storage has generous handles set far enough apart for an elbow to pass between them.',
    'A small enamel panel makes a brighter patch among the room\'s more subdued working surfaces.',
],[
    'The layout leaves short, familiar journeys between preparing, washing, and putting things aside.',
    'A trace of earlier cooking remains beneath the clean surfaces, a warmer smell than the room\'s hard finishes suggest.',
    'The working edge gives company a place to linger without turning every movement into an awkward negotiation.',
    'The room makes a practical kind of welcome, measured in elbow room and surfaces within reach.',
    'Even the decorative touches stay close to the work, adding color without obscuring the kitchen\'s purpose.',
])

scene('shop','institution',[
    'The {counter} sits beneath a shallow display recess framed in {surface} on the {side} side.',
    'A broad strip of {surface} draws the eye toward the {counter} at the {side} end.',
    'The {counter} makes a dogleg beside the {side} wall, separating a compact sales position from the browsing floor.',
    'The {side} displays step down toward a low {counter}, with {surface} tying the fittings together.',
    'A squared pier faced in {surface} stands beside the {counter}, breaking the {side} part of the shop into smaller bays.',
    'The {counter} occupies a shallow angle in the {side} wall, leaving the displays visible from the customer side.',
],[
    'Small label holders repeat along the shelf edges, some bright at the corners and others dulled by handling.',
    'One display groups the goods by size, creating a stepped silhouette against the backing panel.',
    'A narrow mirror at the end of a display repeats the nearest rows into a deeper-looking arrangement.',
    'Packaging makes a mosaic of muted colors, interrupted by a deliberately clearer patch around a featured display.',
    'Fine wire dividers keep neighboring goods apart without hiding their outlines.',
    'A shallow display tray is lined with a softer material than the surrounding fittings.',
    'The upper shelving leaves a generous gap beneath the ceiling, making the crowded lower rows feel less close.',
    'A small handwritten-looking label introduces an uneven note among otherwise regular printed cards.',
],[
    'The arrangement makes browsing feel unhurried, with the sales position always easy to find again.',
    'Cardboard and handled goods lend the shop a dry, familiar smell beneath the cleaner surface finish.',
    'The displays reward attention to small differences, leaving the open floor to carry the ordinary passing trade.',
    'There is enough room for two people to compare impressions without turning the aisles into a meeting room.',
    'The shop has a practical intimacy, bringing a whole collection of choices within a few steps.',
])

scene('library','domestic',[
    'Bookcases frame the {reading table} along the {side} wall, with {surface} outlining their deeper recesses.',
    'The {reading table} sits beneath a shallow arch of shelving on the {side} side.',
    'A break in the {side} shelves leaves room for the {reading table}, backed by a panel of {surface}.',
    'The {side} corner opens around the {reading table}, where lower shelving gives way to {surface}.',
    'A tall divider faced in {surface} screens the {reading table} from the more exposed {side} aisle.',
    'The {reading table} stands a little apart from the {side} shelves, leaving the nearest book spines within a seated glance.',
],[
    'The bindings form uneven bands of faded red, brown, and cloth-gray, with one conspicuously narrow volume between broader neighbors.',
    'Shelf labels use small, careful lettering, their edges softened where readers have brushed past.',
    'A book support has been shaped into a simple leaf, the carved veins visible only at close range.',
    'A narrow display ledge presents several volumes face-out, breaking the long rhythm of spines.',
    'The nearest shelf has adjustable slots along the uprights, a practical detail beneath the more substantial woodwork.',
    'A low stack of oversized books makes a horizontal interruption among the upright rows.',
    'The table has a shallow groove around the working surface, collecting a thin line of paper dust.',
    'Small variations in the shelf depths make the book-lined wall look assembled over more than one period.',
],[
    'Old paper carries a dry sweetness through the close air, with a faint mustiness deeper between the rows.',
    'The shelving breaks up sound, giving a lowered conversation the feeling of a small clearing among books.',
    'The room encourages the eye to settle on one thing at a time, despite the accumulation surrounding it.',
    'There is a patient, scholarly quiet here, made by materials that change more slowly than the people handling them.',
    'The space feels most complete at reading distance, where small titles and the grain of a tabletop become the landscape.',
])

scene('dining','domestic',[
    'A {corner table} sits beyond the main dining arrangement on the {side} side, beneath a band of {surface}.',
    'The {side} wall steps back around a {corner table}, making a quieter setting within the dining room.',
    'A low divider faced in {surface} shelters the {corner table} toward the {side} end.',
    'The {corner table} stands beside a broad decorative panel of {surface}, just off the {side} line of passing chairs.',
    'The dining settings turn slightly toward the {side} end, where the {corner table} has a little more enclosure.',
    'A shallow alcove of {surface} gathers the {corner table} away from the busiest part of the {side} floor.',
],[
    'The chair backs use a simple curved motif that repeats, at a smaller scale, along the nearest table edge.',
    'A narrow runner adds a band of texture across an otherwise clear tabletop.',
    'The smaller settings leave uneven gaps between them, making room for company to choose different distances from the center.',
    'A framed still life picks up the warm colors of the room without competing with the tables.',
    'A small arrangement of folded cloth introduces crisp, pale triangles among the darker furniture.',
    'The tabletop edges are gently rounded, with a darker line following the grain just below the finish.',
    'A decorative plate is mounted above the seated eye line, the glaze crazed into a fine network.',
    'The floor changes texture beneath the dining settings, marking each little island of chairs without enclosing it.',
],[
    'The room brings company close enough for conversation to survive the ordinary sounds of a meal.',
    'A faint trace of cooked food gives the carefully arranged interior a less formal warmth.',
    'The scale favors a long visit, with the surrounding details left to fill comfortable pauses.',
    'The small differences between settings keep the dining room from feeling like a single repeated arrangement.',
    'Nothing asks a group to hurry; even the spaces around the chairs seem measured for people lingering.',
])

scene('cafe','domestic',[
    'The {counter} faces small {tables} from the {side} side, with {surface} warming the fittings behind it.',
    'A curved {counter} occupies the {side} corner, the nearest {tables} set just beyond the change in flooring.',
    'The {side} wall gathers the {counter} beneath a broad panel of {surface}, leaving the {tables} in a looser arrangement.',
    'A low display shelf of {surface} backs the {counter} at the {side} end of the cafe.',
    'The {counter} cuts a short diagonal across the {side} corner, with small {tables} turned toward the open room.',
    'The {side} {tables} sit near a shallow wall recess, where the finish changes to {surface}.',
],[
    'Cup-shaped marks form pale crescents beneath the table finish, overlapping the grain like incomplete rings.',
    'A small chalkboard panel carries the dust of earlier lettering along the lower edge.',
    'Mismatched chair backs add a little variation to the cafe\'s close, practical layout.',
    'A narrow shelf presents cups in short groups, their handles making repeated hooks against the backing.',
    'A framed print of a leaf has been hung slightly below the surrounding decoration.',
    'The nearest table has a darker inset at the center, just large enough to gather a few cups.',
    'A cloth-covered notice strip makes a patchwork of paper corners and pinheads.',
    'The counter trim has a subtle ripple in the finish, visible where the surface catches a reflection.',
],[
    'The coffee smell has settled into the room, outlasting any single cup brought to a table.',
    'The close furniture makes it easy for a short stop to become a longer conversation.',
    'Hard cup-sized sounds would carry clearly here, while the softer furniture keeps voices comfortably near.',
    'The cafe has the pleasant scale of an ordinary pause, with enough detail to notice between sips.',
    'The arrangements leave room for both sociable company and someone content to watch the room from a small table.',
])

scene('tavern','domestic',[
    'The {bar} follows the {side} wall beneath substantial trim of {surface}, with {tables} set farther back.',
    'A squared return gives the {bar} a sheltered end on the {side} side, framed in {surface}.',
    'The {side} {tables} rest below a broad decorative panel of {surface}, a little removed from the {bar}.',
    'The {bar} turns around the {side} corner, giving the tavern two slightly different angles of conversation.',
    'A low bulkhead finished in {surface} draws the ceiling closer above the {side} end of the {bar}.',
    'The {bar} stands against an inset section of the {side} wall, leaving a generous public edge before the {tables}.',
],[
    'Old drink rings lie beneath the finish in overlapping circles, some broad and pale, others small and dark.',
    'A decorative mirror repeats the nearest table backs in a softly imperfect reflection.',
    'A narrow carved border uses a pattern of leaves, interrupted where two lengths of trim meet.',
    'The foot rail has a brighter wear through the middle than at either end.',
    'A framed piece of local-looking memorabilia occupies a place of honor disproportionate to the size of the frame.',
    'The table legs have broad feet, giving the furniture a stubbornly stable appearance.',
    'A small recess in the wall makes a dark, shallow pocket above the level of the chairs.',
    'The counter has a softly rounded lip, worn to a different sheen from the wider working surface.',
],[
    'Wood polish and old beer mingle in the close air, the familiar smell of conversations that ran beyond one drink.',
    'The room offers a choice between the shared counter and the smaller company gathered around a table.',
    'The heavier furniture absorbs some of the room\'s bustle, leaving the corners suited to lowered voices.',
    'The proportions are comfortably unceremonious, built around resting elbows rather than making an entrance.',
    'There is a settled sociability to the place, visible in the surfaces shaped by years of people lingering.',
])

scene('club','domestic',[
    'A low {sofa} rests against the {side} wall below a dark-edged panel of {surface}.',
    'The {side} corner gathers a {sofa} beneath an angled decorative section faced in {surface}.',
    'A strip of {surface} separates the {sofa} from the broader activity floor on the {side} side.',
    'The {sofa} sits within a shallow recess at the {side} end, where the ceiling comes down a little lower.',
    'The {side} wall breaks into broad panels of {surface}, leaving the {sofa} sheltered between the strongest vertical lines.',
    'A low divider turns the {sofa} slightly away from the open floor at the {side} end.',
],[
    'The decorative surfaces alternate between matte and glossy finishes, changing the room\'s depth with the viewing angle.',
    'A repeating fan-shaped motif makes a theatrical border around the quieter part of the floor.',
    'The upholstery has a fine sheen along the raised seams, with a heavier texture between them.',
    'A narrow mirror breaks the nearby furniture into slivers rather than returning a complete reflection.',
    'The floor carries intersecting arcs of wear, the accumulated traces of turns rather than straight crossings.',
    'A strip of padded wall covering muffles the harder surfaces around it.',
    'The trim uses an exaggerated curve where the rest of the room keeps to straight lines.',
    'A shallow ledge traces the wall at elbow height, interrupted by the broader decorative panels.',
],[
    'The room is shaped for company that wants to be seen and for company that would rather watch from the edge.',
    'Old perfume lingers in the fabric, a softer note beneath the room\'s hard, theatrical finishes.',
    'The open middle makes a small movement conspicuous, while the upholstery gives the seated corner a closer scale.',
    'Even without a performance underway, the contrast between the open floor and the tucked-away seating suggests anticipation.',
    'The furnishings favor company leaning close, leaving the wider room to carry the larger gestures.',
])

scene('foyer','institution',[
    'A {waiting bench} rests along the {side} wall beneath a broad band of {surface}.',
    'The {side} corner steps inward around the {waiting bench}, leaving the main arrival space clear.',
    'A squared pier faced in {surface} separates the {waiting bench} from the {side} line of passage.',
    'The {waiting bench} sits beneath a shallow wall recess on the {side} side, where the finish changes to {surface}.',
    'A low decorative panel of {surface} frames the {waiting bench} toward the {side} end of the reception space.',
    'The {side} floor widens beside the {waiting bench}, making a small pause within the larger circulation space.',
],[
    'A narrow directory panel is arranged in careful rows, with slightly different shades behind the oldest labels.',
    'A mat with a simple border makes a darker rectangle along the busiest route across the floor.',
    'The wall trim turns around the corners with unusually broad, softly rounded joints.',
    'A framed abstract print offers a restrained patch of color at seated eye level.',
    'The floor pattern shifts by half a tile near the edge, a small irregularity in an otherwise formal arrangement.',
    'A shallow display recess holds a single decorative object, giving the surrounding blank surface a deliberate focus.',
    'The lower wall finish is sturdier than the panels above, built to survive bags and passing coats.',
    'An inset notice surface is bordered by a fine line of darker trim.',
],[
    'The arrangement gives an arrival somewhere to pause before deciding how to become part of the room.',
    'The public surfaces carry a faint polish smell, with the quieter seating set just beyond the main flow.',
    'The space balances welcome with a little institutional distance, keeping arrivals plainly in view.',
    'The broad center makes movement legible, while the bench offers the more patient perspective of waiting.',
    'A few carefully placed fittings do most of the work, leaving the room open enough to take in at a glance.',
])

scene('corridor','institution',[
    'A band of {surface} follows the {side} wall, turning a plain passage into a sequence of long, horizontal lines.',
    'The {side} wall steps inward around a shallow structural pier faced in {surface}.',
    'A rectangular recess interrupts the {side} side of the corridor, framed by a narrow border of {surface}.',
    'The ceiling drops slightly toward the {side} wall, where {surface} picks out the change in level.',
    'A vertical seam divides the {side} finish into two unequal panels of {surface}.',
    'The {side} edge of the floor follows a low, rounded skirting finished in {surface}.',
],[
    'The floor pattern shifts by a small fraction at an old join, making the repair easier to feel with the eye than to measure.',
    'A simple wall plate sits a little above the surrounding trim, the corners softly rounded.',
    'The upper finish has a finer texture than the more durable strip close to shoe height.',
    'A line of shallow grooves gives the lower wall a rhythm that changes as the passage is viewed end-on.',
    'One broad panel is set back just far enough to catch a thin border of shadow.',
    'A narrow patch in the flooring crosses the usual line of travel at a diagonal.',
    'The ceiling joints converge slightly off-center, lending the passage an unobtrusive asymmetry.',
    'Small changes in the grain of the trim reveal where separate lengths have been fitted together.',
],[
    'The clear passage carries sound farther than the close walls first suggest.',
    'The long proportions draw the eye past each small interruption in the wall, making the far end feel slightly removed.',
    'The repeated lines give the passage a quiet momentum, drawing attention along the building rather than into the margins.',
    'The restrained details become noticeable during a pause, then fall back into the ordinary business of passing through.',
    'The enclosure makes a small sound feel near even when the source lies beyond the immediate view.',
])

scene('stairs','institution',[
    'The stair structure presses close to the {side} wall, where a band of {surface} follows the change in height.',
    'A broad section of {surface} frames the {side} edge of the stairs beneath a sharply angled ceiling.',
    'The {side} treads meet a low structural return faced in {surface}.',
    'A shallow recess in the {side} wall breaks the repeating geometry of the stair, exposing a different plane of {surface}.',
    'The {side} edge is emphasized by a narrow strip of {surface}, making each change of level distinct.',
    'A solid pier rises beside the {side} stair structure, the finish of {surface} contrasting with the exposed tread edges.',
],[
    'The nearest treads have gently rounded noses, with narrower dark lines where the risers meet them.',
    'A handrail changes angle at a carefully fitted joint, the curve smoother than the straight lengths around it.',
    'The supporting structure leaves a triangular pocket below the nearest change in level.',
    'A narrow seam follows the underside of the stair, emphasizing the weight carried above it.',
    'The visible fastenings sit in a repeated line, each one slightly recessed into the supporting surface.',
    'The wall finish has been cut closely around the stair profile, leaving a fine zigzag at the join.',
    'A broader tread interrupts the climb, the corners polished smoother than the wide, shallow center.',
    'The inner edge feels tighter than the outer one, a small difference made conspicuous by the repeated steps.',
],[
    'The enclosure gives each small sound a short, climbing echo.',
    'Everything here is organized around a change in height, leaving little reason to linger in the line of passage.',
    'The repeated angles make the structure easy to follow close at hand and surprisingly intricate from a distance.',
    'The cramped margins put the building\'s construction within reach, from the rail to the underside of the nearest tread.',
    'The stair keeps the room in motion even while empty, a sequence of surfaces made for the next step.',
])

scene('mill','industrial',[
    'A broad machine foundation interrupts the {side} floor beneath columns faced in {surface}.',
    'The {side} bay contains the ribbed housing of a rolling stand, framed by heavy lengths of {surface}.',
    'A recessed inspection pit breaks the {side} working surface, with {surface} tracing the solid edges.',
    'The {side} section is crossed by the massive support frame of an overhead handling assembly.',
    'A furnace housing dominates the {side} bay, the surrounding {surface} marked by the different expansion of neighboring materials.',
    'Broad roller supports line the {side} floor, their repeated profiles standing against structural spans of {surface}.',
    'A square maintenance recess opens within the {side} machinery housing, exposing layered plates and {surface}.',
    'The {side} floor broadens around a loading cradle, the heavy supports picking out a band of {surface}.',
],[
    'Bolt heads form a close ring around a blank inspection cover, with deeper metal showing between the fitted plates.',
    'A line of old handling scars crosses the concrete at an angle to the machinery foundations.',
    'A heavy wheel is mounted beside a guarded mechanism, the spokes broad enough to read clearly from across the bay.',
    'Channels in the floor turn around a rectangular foundation before rejoining the broader working surface.',
    'A row of thick brackets marks the course of a former handling line along the nearest support.',
    'The lower steelwork has a darker scale than the surfaces above, revealing the different lives of heat, oil, and ordinary air.',
    'A broad metal shield has been fitted with overlapping edges, each plate carrying a slightly different tone.',
    'A shallow trough lies beneath the machinery edge, collecting fine industrial grit in a narrow band.',
    'The nearest beam carries a welded patch with a distinctive crescent at one corner.',
    'A repeated pattern of mounting holes remains visible across a thick, otherwise plain plate.',
    'A low retaining curb turns around the heavier apparatus, separating the foundations from the traveled floor.',
    'A stout rack holds fixed supports at different heights, creating an uneven skyline of blunt metal shapes.',
],[
    'Concrete dust and worked metal give the bay a dry, heavy smell; the great spans return sound in distant layers.',
    'The machinery gives this portion of the mill a different scale from a mere room, with human-sized space left between the foundations.',
    'The arrangement records the movement of immense loads, even where only the supports remain in view.',
    'The open height makes the lower structures feel heavier, each one an island within the steel frame.',
    'The industrial surfaces have several kinds of wear, separating the places touched by hands from those shaped by heat and weight.',
])

scene('warehouse','industrial',[
    'A broad storage bay opens along the {side} wall beneath structural spans of {surface}.',
    'The {side} floor is divided by a row of stout supports, their lower faces showing {surface}.',
    'A reinforced wall panel of {surface} gives the {side} end a blunt, practical finish.',
    'The {side} corner widens around a low loading platform edged with {surface}.',
    'A deep structural recess breaks the {side} wall into a narrower bay behind the main floor.',
    'The {side} roof supports meet above a squared pier, exposing the layered construction beneath the {surface}.',
],[
    'Parallel handling marks cross the floor, ending in a darker patch near the heavier structure.',
    'The wall carries the faint outlines of older storage divisions, visible beneath the more recent finish.',
    'A row of fixed metal hooks follows a support at a height intended for more than casual reach.',
    'The nearest joints have wide overlapping plates, with bolt heads making a regular pattern around them.',
    'A protective rail sits close to the base of the structure, rubbed brighter where bulky loads have passed.',
    'Dust gathers in a long wedge beneath the deepest overhang.',
    'A narrow strip of floor has a rougher texture, giving the working surface a clear change underfoot.',
    'The lower wall is reinforced in broad sections, each one slightly offset from the panel above.',
],[
    'The open spans make a modest sound travel farther than expected, returning it with a hollow edge.',
    'The room smells of dry concrete and sheltered storage, with little softness among the practical surfaces.',
    'The clear center preserves the wide turning arcs of old loads, with the finest dust caught safely beneath the shelving.',
    'The scale belongs to loads and working clearances, leaving the smaller marks of human use near the edges.',
    'The clear bays show their purpose through structure rather than decoration.',
])

scene('underground','stone',[
    'A low structural arch of {surface} draws the {side} wall close to the passage.',
    'The {side} masonry thickens around a squared support, exposing rougher {surface} beneath the finished edge.',
    'A shallow drainage recess follows the {side} floor beside a wall of {surface}.',
    'The {side} wall changes from broad blocks to smaller fitted pieces, leaving an irregular seam through the {surface}.',
    'A narrow shelf of {surface} projects from the {side} base of the wall, just above the traveled ground.',
    'The {side} ceiling curves down into a heavy pier, concentrating the enclosing weight in a mass of {surface}.',
],[
    'Pale mineral fans spread beneath a deep joint, stopping short of the grittier surface below.',
    'A repaired section uses smaller stones fitted around the older work like a rough mosaic.',
    'Fine sediment marks a shallow depression where water has gathered and receded.',
    'The wall keeps a series of blunt tool marks, their direction changing across separate blocks.',
    'A dark seam crosses the floor at an angle, disappearing beneath the nearest structural mass.',
    'The lower surfaces have a smoother wear than the rough material above shoulder height.',
    'A small recess holds a deeper pocket of darkness within the otherwise readable wall.',
    'The visible joints narrow toward the ceiling, giving the enclosure a compressed, almost folded shape.',
],[
    'The air carries a cool mineral damp, and sounds return with the close insistence of an enclosed passage.',
    'The building above is apparent as weight rather than a view, pressing the proportions down around the traveled floor.',
    'The narrow margins make the enclosing structure feel close, every seam and mineral stain held within easy reach.',
    'The sheltered surfaces seem to keep the memory of moisture long after the visible traces have faded.',
    'The confined scale makes nearby details vivid while leaving the deeper enclosure difficult to judge.',
])

scene('cave','stone',[
    'A folded ridge of {surface} rises from the {side} floor and disappears into the enclosing rock.',
    'The {side} wall opens into a shallow natural hollow lined with {surface}.',
    'A slanted seam of {surface} divides the {side} rock face into two differently grained masses.',
    'The {side} ceiling lowers around a rounded projection, the surface layered like folded {surface}.',
    'A shelf of {surface} breaks the {side} slope, with loose fragments gathered beneath the lip.',
    'The {side} rock narrows into a buttress whose rough grain contrasts with the smoother {surface} beside it.',
],[
    'Small mineral beads cling beneath an overhang, their pale edges distinct against the darker stone.',
    'The floor holds a fan of broken chips, grading from blunt fragments to fine grit.',
    'A branching stain follows a hidden route through the rock before spreading into a wider patch.',
    'The wall carries shallow ripples that look almost worked by hand until their irregular spacing becomes clear.',
    'A rounded pocket holds finer sediment than the rough ground surrounding it.',
    'The nearest fracture exposes a fresher color beneath the weathered outer skin.',
    'A thin crust bridges a narrow crack, fragile-looking beside the mass on either side.',
    'The stone changes texture across a crooked line, from fine grain to small, glittering inclusions.',
],[
    'The cave smells of cool stone and sheltered grit, with no domestic softness to break the enclosure.',
    'The rock gives sound an uneven return, sometimes close and sometimes swallowed by the surrounding folds.',
    'The irregular surfaces offer plenty for the eye to follow without resolving into any deliberate arrangement.',
    'The enclosed air makes the smallest exposed seam feel like part of a much larger depth.',
    'The natural shapes remain stubbornly indifferent to a human-sized sense of comfort or symmetry.',
])

scene('forest','earth',[
    'A broad root shoulder breaks the {side} ground, lifting a skin of {surface} above the leaf litter.',
    'The {side} undergrowth gathers around a fallen limb whose lower edge has begun to disappear beneath {surface}.',
    'A narrow hollow in the {side} ground holds a deeper layer of {surface} between the roots.',
    'The {side} trunks lean around a small break in the canopy, their bases ringed with {surface}.',
    'A forked trunk marks the {side} margin, with {surface} caught in the sheltered angle below it.',
    'The {side} forest floor rises over buried timber, exposing a long irregular seam of {surface}.',
],[
    'Lichen makes pale islands across the rough bark, changing shape where the grain turns around a knot.',
    'Fine twigs lie crosswise over broader branches, building a delicate lattice close to the soil.',
    'A leaf has caught upright between two roots, the dry veins more visible than the remaining color.',
    'Small shelves of fungus cling to a fallen branch, their layered edges softer than the wood beneath them.',
    'The nearest bark peels in narrow curls, showing a smoother tone under the weathered outer layer.',
    'New growth threads through an older tangle, making a finer green texture among the heavier stems.',
    'A shallow impression in the ground has filled with the smaller fragments of fallen leaves.',
    'One exposed root splits around a stone, the two lengths joining again beyond the obstruction.',
],[
    'Leaf mold gives the sheltered ground a rich smell, while the overlapping growth breaks the distance into small glimpses.',
    'The woodland is close without becoming a room; the enclosure belongs to growth rather than walls.',
    'The ground keeps several stages of decay visible at once, from crisp leaves to timber almost returned to soil.',
    'The nearest textures are easy to follow, but the tangle beyond them resists a clear, uninterrupted view.',
    'There is little here arranged for a visitor, only the patient pressure of plants occupying the available space.',
])

scene('exterior','stone',[
    'A low curb of {surface} follows the {side} margin of the open ground.',
    'The {side} surface changes around a broad repair edged with {surface}.',
    'A narrow strip of {surface} marks the {side} boundary between the traveled ground and the rougher margin.',
    'The {side} edge broadens beside a shallow drainage seam cut through {surface}.',
    'A squared patch of {surface} interrupts the otherwise uneven {side} surface.',
    'The {side} margin rises gently against a low retaining edge of {surface}.',
],[
    'Fine grit gathers in a branching crack, leaving the harder surface clear between the lines.',
    'The ground retains a faint arc of wear where passing traffic has favored the same turn.',
    'A small tuft of stubborn growth has found a pocket between two differently finished surfaces.',
    'An older stain has faded to a soft outline, most distinct where the surrounding ground changes texture.',
    'The exposed edges are rounded more heavily on one side than the other.',
    'Small stones have collected in the shallowest depression, sorted into a rough crescent.',
    'A narrow join runs slightly off the line of the surrounding work, recording an earlier patch.',
    'The immediate ground is clearest through the middle, where ordinary passage has kept the margins at bay.',
],[
    'The open setting leaves little to contain sound, with the nearest boundaries giving the space a local scale.',
    'This is ground meant to be crossed or briefly paused upon, shaped by ordinary use rather than furnishings.',
    'The exposed surfaces carry a small history of repairs, each one aging a little differently from the last.',
    'The details are modest but distinct, visible in the joins between maintained ground and the less-tended edges.',
    'Nothing closes the space overhead; the surrounding forms frame the ground without turning it into an interior.',
])

scene('air','stone',[
    'Toward the {side}, the nearest shapes below form a broken outline around a pale patch of {surface}.',
    'The {side} view opens above a narrow line of {surface}, reducing the ground to texture and proportion.',
    'A distinct edge of {surface} lies far below on the {side} side, a small reference point within the open height.',
    'The {side} surroundings fall away beyond a broad shape of {surface}, leaving the air itself unenclosed.',
    'The {side} view gathers the nearer ground into overlapping bands, one pale strip of {surface} standing out among them.',
    'A small angular patch of {surface} anchors the {side} view before the more distant forms lose their detail.',
],[
    'Nearby outlines remain sharper than the forms beyond them, making the depth apparent without giving it an easy measure.',
    'The spaces between the lower shapes look narrower from this height than their separate edges suggest.',
    'An isolated vertical form below interrupts the broader pattern, drawing attention before becoming small again.',
    'The surrounding emptiness gives every visible edge an unusual emphasis.',
    'A change in angle would rearrange the overlapping shapes more quickly than an eye expects.',
    'The nearer surfaces show their upper faces, revealing outlines usually lost when viewed from the ground.',
],[
    'There is no floor here, only the exposed scale of open air and the distant arrangement beneath it.',
    'Height strips familiar things of their ordinary size, leaving the sky immense around a few small points of reference.',
    'The open space offers no enclosing surface to return a sound or make the distance feel comfortably near.',
    'It\'s a place of depth rather than enclosure, with the nearest solid forms kept distinctly below.',
])

scene('garden','earth',[
    'The {side} planting curves around a shallow bed of {surface}, breaking the cultivated ground into a softer outline.',
    'A low ridge of {surface} divides the {side} growth into two differently textured drifts.',
    'The {side} stems gather around a broad patch of {surface}, their smaller leaves overlapping above the soil.',
    'A narrow border follows the {side} planting, with {surface} filling the intervals between the roots.',
    'The {side} bed steps up gently, exposing a darker band of {surface} beneath the lower leaves.',
    'A small break in the {side} planting reveals {surface} beneath a close screen of stems.',
],[
    'Fine leaves make a feathery texture beside broader, waxier blades.',
    'A curling tendril has wound around an older stem, repeating the same tight spiral several times.',
    'One low plant carries a pale border around each leaf, making a delicate pattern close to the ground.',
    'The worked soil changes color around the nearest roots, revealing the different places moisture settles.',
    'A small marker leans among the stems, almost lost at the height of the lower leaves.',
    'The planting leaves an irregular gap around a stone rather than concealing it.',
    'Newer shoots have a softer color than the tougher growth beneath them.',
    'The edge is carefully tended without being perfectly straight, retaining the small irregularities of growing things.',
],[
    'The cultivated ground smells richly of earth, with a greener trace where leaves and stems meet at close quarters.',
    'The planting rewards a slow look, offering different textures at the scale of a hand rather than a whole landscape.',
    'The arrangement is deliberate but never quite rigid; each plant has found a slightly different way to occupy it.',
    'The plants provide the focus here, leaving the ordinary gaps between them as part of the setting.',
])

scene('water','stone',[
    'Toward the {side}, the water deepens over a submerged band of {surface}.',
    'A pale shape of {surface} interrupts the {side} depths before the surrounding water softens the outline.',
    'The {side} water gathers above an uneven shelf of {surface}, breaking the bottom into overlapping planes.',
    'A narrow seam of {surface} remains visible beneath the {side} water, fading where the depth increases.',
    'The {side} bed slopes away from a low rise of {surface}, leaving a darker reach beyond it.',
    'A small hollow lined with {surface} lies beneath the {side} water, distinct from the surrounding sediment.',
],[
    'Fine particles hang between the nearer shapes, blurring the smallest details before the larger outlines disappear.',
    'The surface breaks reflections into small, uneven pieces that never settle into a single picture.',
    'Soft sediment gathers at the lower edges of the submerged forms.',
    'The nearer water keeps a clearer color than the deeper reach beyond it.',
    'Small ridges on the bottom remain visible until a change in the surface interrupts the view.',
    'The overlap of water and submerged ground makes distances difficult to judge by sight alone.',
],[
    'The surrounding water lends everything a softened depth, with no dry standing place within the immediate reach.',
    'The open water gives a view without offering the certainty of firm ground beneath it.',
    'Even the clearest shape seems held at a remove by the layers between it and the surface.',
    'The water remains the defining feature, gathering the smaller contours into one continuous expanse.',
])

scene('vehicle','institution',[
    'The passenger {seats} face a {side} interior panel edged with {surface}.',
    'A curved trim panel of {surface} frames the {seats} on the {side} side of the vehicle.',
    'The {side} passenger space narrows beside the {seats}, where {surface} outlines a shallow fitted recess.',
    'The {seats} sit close to the {side} lining, beneath a narrow strip of {surface}.',
    'A broad inset of {surface} breaks up the {side} paneling beside the passenger {seats}.',
    'The {side} bodywork curves around the {seats}, fitting each panel closely against a border of {surface}.',
],[
    'A stitched diamond pattern runs through the seat backs, fading to a smoother texture near the edges.',
    'The nearest armrest has a small circular indentation in the padding.',
    'A map pocket follows the back of a seat, the upper edge stretched into a shallow curve.',
    'The interior lining has a subtle woven pattern that becomes visible at close range.',
    'A rubber floor mat carries a series of broad parallel ribs, with fine dust held between them.',
    'The nearest seat seam changes direction around a carefully fitted corner.',
    'A small vent has rounded fins, their edges darker than the surrounding panel.',
    'The handle recess has a softer finish than the harder trim surrounding it.',
    'A pale repair stitch crosses one short section of the upholstery without matching the original spacing.',
    'The seat backs have broad, shallow pockets that deepen the shadows between the fitted cushions.',
],[
    'The enclosed air carries fabric and rubber, the familiar smell of a small space used for many journeys.',
    'The close seating brings a traveling companion within easy speaking distance, with little room wasted between the fittings.',
    'The vehicle feels compact even while still, every surface shaped around the practical business of carrying people.',
    'The padded interior softens the harder shell around it without disguising the tight passenger proportions.',
    'It\'s a small enclosure full of fitted curves, made to keep company close while the wider world lies outside.',
])

# Related spaces share suitable construction details while keeping a distinct
# focal vocabulary. Their saved descriptions still receive separate selections.
def related(kind, parent, focus, detail=None, atmosphere=None):
    source=SCENES[parent]
    scene(kind,source['family'],focus,detail or source['detail'],atmosphere or source['atmosphere'])

related('hall','corridor',[
    'A broad panel of {surface} gives the {side} wall a quiet focus within the otherwise open hall.',
    'The {side} ceiling steps down above a squared structural pier faced in {surface}.',
    'A shallow wall recess on the {side} side is framed by a generous border of {surface}.',
    'The {side} floor widens around a low projection from the wall, making the open interior slightly asymmetrical.',
    'A long strip of {surface} follows the {side} side at shoulder height, breaking the plain wall into two proportions.',
])
related('storage','warehouse',[
    'Close storage fittings follow the {side} wall beneath a plain backing of {surface}.',
    'The {side} shelves are divided into uneven bays, their stout supports outlined in {surface}.',
    'A deep storage recess breaks the {side} wall, with {surface} covering the heavier lower fittings.',
    'The {side} storage narrows around a broad structural post, leaving a clear working strip beside it.',
    'A low bank of closed compartments follows the {side} wall below a long surface of {surface}.',
],atmosphere=[
    'The dry, enclosed air smells of things put aside, with the clear floor reserved for reaching and carrying them.',
    'The shelves have the dry smell of old packaging, strongest where their closely fitted backs meet the wall.',
    'The practical fittings leave little decorative surplus, making the small signs of handling unusually visible.',
    'The storage has a patient stillness, an arrangement waiting for the next ordinary task to require something.',
])
related('pantry','storage',[
    'Food-storage shelves line the {side} wall, with {surface} keeping the backing plain and washable.',
    'The {side} storage is divided into shallow compartments beneath a broad strip of {surface}.',
    'A narrow shelving return makes the {side} corner more closely enclosed than the central standing strip.',
    'The {side} lower fittings have sturdy, closely joined fronts framed in {surface}.',
],detail=[
    'Small labels are set below the storage divisions, their regular spacing interrupted by a wider central compartment.',
    'The shelf edges are raised slightly, giving the stored shapes a clear boundary.',
    'A broad lower recess has a smoother finish than the narrower shelves above it.',
    'The nearest joints have been sealed closely, leaving few exposed gaps around the fittings.',
    'The lower shelves are deeper than the upper ones, making a stepped profile beside the clear floor.',
])
related('workshop','kitchen',[
    'A broad {worktable} occupies the {side} half of the workshop beneath a strip of {surface}.',
    'The {worktable} stands beside a deep working recess on the {side} side, framed in {surface}.',
    'A low storage return of {surface} backs the {worktable} against the {side} wall.',
    'The {side} working surfaces turn inward around a stout {worktable}, leaving the busiest edge clear.',
],detail=[
    'Fine tool cuts cross an older patch of staining, recording several kinds of careful work on the same surface.',
    'A rack of fixed supports leaves a pattern of narrow shadows against the backing.',
    'The nearest work surface has a replaceable top fitted within a sturdier frame.',
    'Small shavings and dried specks have settled into the deepest joints beyond the ordinary sweep of a hand.',
    'A clamping edge follows one side of the working surface, the metal worn brighter around the fastening points.',
    'A strip of sacrificial wood has been fastened to the nearest edge, showing more marks than the surface it protects.',
],atmosphere=[
    'The room smells of handled materials and dry work, with the arrangement bringing a project within easy reach.',
    'The working space is practical without feeling impersonal; small marks preserve the decisions of earlier hands.',
    'The table gives company a shared view of the work, leaving the surrounding floor for movement.',
    'The room rewards attention at the scale of a cut edge, a measured line, or a carefully fitted joint.',
])
related('laboratory','office',[
    'A washable {workbench} runs along the {side} wall beneath a broad panel of {surface}.',
    'The {side} research stations turn around a central {workbench}, with {surface} outlining the lower fittings.',
    'The {workbench} sits within a deep working recess on the {side} side, separated from the clearer central floor.',
    'A low divider faced in {surface} distinguishes the {workbench} from the {side} passage between stations.',
],detail=[
    'The work surface has a shallow raised edge intended to keep a small spill from reaching the floor.',
    'Fixed racks break the nearest station into repeated narrow compartments.',
    'The polished fittings have a faint haze from repeated cleaning, most visible around the handling points.',
    'A diagram panel uses fine ruled lines and careful spacing, making a dense arrangement of small labels.',
    'The lower cupboards have flush fronts, leaving the working edges unusually easy to follow.',
    'A narrow trough runs beneath one section of the work surface before disappearing into the fitted structure.',
],atmosphere=[
    'The laboratory carries a sharp trace of cleaning, and the uncluttered stations make each small irregularity conspicuous.',
    'The arrangement suggests work that depends on keeping one thing distinct from the next.',
    'There is a controlled quiet here, shaped by clear surfaces and deliberately separated working positions.',
    'The room brings complicated work down to a series of small, carefully bounded stations.',
])
related('treatment','laboratory',[
    'A {treatment table} sits within a washable recess on the {side} side, backed by {surface}.',
    'The {side} treatment position is organized around a narrow {treatment table} and a broad panel of {surface}.',
    'A low screen divides the {treatment table} from the {side} fittings, keeping the immediate working space clear.',
    'The {treatment table} lies beneath a shallow ceiling step at the {side} end, where {surface} emphasizes the clinical finish.',
],atmosphere=[
    'The room has the close scale of a treatment rather than a waiting space, with little to distract from the central working position.',
    'Antiseptic leaves a sharp edge in the air, and the clear surfaces make the enclosure feel deliberately exposed.',
    'The practical arrangement offers privacy through separation, keeping the clinical work close and the surrounding floor spare.',
    'The fittings bring the room down to the reach of careful hands, with each surface easy to see and clean.',
])
related('clinic','foyer',[
    'A row of {waiting chairs} follows the {side} wall beneath washable panels of {surface}.',
    'The {side} public margin gathers {waiting chairs} just beyond the clinical floor, with {surface} framing the fittings.',
    'A low partition faced in {surface} separates the {waiting chairs} from the clearer {side} working space.',
    'The {waiting chairs} rest in a shallow recess on the {side} side, leaving the clinical route unobstructed.',
],atmosphere=[
    'The air carries a restrained medicinal smell, with the public seating set apart from the work of the clinic.',
    'The pale, washable surfaces give waiting a particular clarity, leaving small sounds unusually distinct.',
    'The room offers a place for company to remain nearby without becoming part of the treatment space.',
    'The seating makes room for patience, while the spare floor keeps the practical purpose of the clinic apparent.',
])
related('meeting','office',[
    'The {meeting table} faces a broad panel of {surface} at the {side} end of the room.',
    'Chairs gather around the {meeting table}, with the {side} seats set beneath a shallow wall recess.',
    'The {meeting table} lies slightly toward the {side} wall, where {surface} gives the formal arrangement a calmer edge.',
    'A low section of ceiling draws attention toward the {side} end of the {meeting table}.',
],detail=[
    'The chair backs have an understated repeating shape, making the differences in spacing more noticeable than the furniture itself.',
    'A broad display panel leaves a clear rectangle above the seated eye line.',
    'The tabletop has a darker border that joins at carefully matched corners.',
    'A narrow inset runs down the middle of the table, dividing the shared surface without blocking a view across it.',
    'The nearest chairs have softly rounded arms, their practical comfort tempered by the room\'s formal arrangement.',
])
related('classroom','office',[
    'The {front desk} faces the teaching surface on the {side} side, with {rear desks} arranged behind it.',
    'A band of {surface} frames the teaching space beyond the {front desk}, giving the {side} end a clear focus.',
    'The {side} student rows begin at the {front desk}, while the {rear desks} sit beyond a wider gap in the floor.',
    'The {front desk} occupies the most exposed position below the {side} teaching panel, facing away from the {rear desks}.',
],detail=[
    'Shallow scratches survive on the student desktops, a small record of waiting hands beneath the formal lesson space.',
    'A display border uses a row of narrow panels, each one set at the same height above the desks.',
    'The nearest desk has a shallow groove along the upper edge of the working surface.',
    'An instructional diagram has been arranged in a careful sequence, drawing the eye from one small section to the next.',
    'The desks leave a wider aisle through one side of the room than the other.',
    'The teaching surface has a fine border of older residue, visible where the central area has been repeatedly cleared.',
],atmosphere=[
    'The room makes the difference between the front and back of a lesson tangible, without needing any further divisions.',
    'The furniture turns attention toward instruction, while the small desktop marks tell a less formal history.',
    'Hard surfaces give every scrape a clear presence, making even an idle movement noticeable.',
    'The classroom is ordinary at first glance, then full of small evidence of students occupying the same places differently.',
])
related('cell','underground',[
    'A narrow {bench} stands against the {side} boundary beneath a plain surface of {surface}.',
    'The {side} enclosure thickens around a low {bench}, leaving only a modest clear patch of floor.',
    'A shallow recess in the {side} wall contains the {bench}, framed by heavier {surface}.',
    'The {bench} occupies the {side} edge, where the enclosing surfaces meet at a blunt, close angle.',
],detail=[
    'Small scratches gather near the height of a resting hand, making an uneven patch on the otherwise plain surface.',
    'The floor has a smoother wear along the shortest route between the boundaries.',
    'The nearest joint is packed flat, denying the rough surface even a useful-looking recess.',
    'A small dark stain has spread along the lowest seam without reaching the clearer middle of the floor.',
    'The boundaries repeat the same few hard shapes from every available angle.',
],atmosphere=[
    'The limited floor makes a small movement feel like a complete circuit of the enclosure.',
    'There is little here to distract an eye; the room makes the same edges available again and again.',
    'The bench offers a place to sit without making the confinement comfortable.',
    'The hard enclosure keeps sound close, returning the smallest scrape with an unwelcome clarity.',
])
related('chapel','cave',[
    'The {side} end is arranged around a recessed devotional panel framed in {surface}.',
    'A broad arch of {surface} gives the {side} place of worship a solemn, compact outline.',
    'The {side} floor opens before a raised devotional surface backed by carefully fitted {surface}.',
    'A narrow decorative band leads toward the {side} observance space, where {surface} gives the room a heavier focus.',
],detail=[
    'A simple repeating motif follows the nearest border, the pattern becoming finer toward the center.',
    'Small traces of old wax sit in the deepest joints beneath the ceremonial fittings.',
    'The surrounding decoration leaves deliberate areas of plain surface between the more intricate work.',
    'The nearest carved edge has been rounded by age, softening the original sharpness of the pattern.',
    'A shallow niche holds a restrained symbolic arrangement rather than filling the wall with ornament.',
],atmosphere=[
    'The spare arrangement gives each carved edge a patient weight, allowing the smallest detail to hold the eye.',
    'The proportions make small sounds distinct, lending a simple movement the weight of an interruption.',
    'The arrangement asks attention of the room without prescribing what anyone must feel in response.',
    'The heavier materials give the devotional details a quiet permanence.',
])
related('gallery','office',[
    'Display cases stand along the {side} wall below a restrained panel of {surface}.',
    'A broad exhibit recess interrupts the {side} wall, framed by an understated border of {surface}.',
    'The {side} displays step around a squared pier, leaving each grouping a different depth within the gallery.',
    'A low display island occupies the {side} half, with the surrounding {surface} kept deliberately plain.',
],detail=[
    'The labels are set below the exhibits, giving the objects room to catch attention before the explanations do.',
    'The glass holds a faint second reflection along the edges, separating the viewer from the objects within.',
    'One case uses a sloping backing, presenting the smaller details at an unusually clear angle.',
    'The exhibit mounts alternate in height, making a measured rhythm through the collection.',
    'A narrow panel offers a sequence of small images, their spacing more important than any surrounding ornament.',
    'The backing changes texture behind a featured piece, isolating it without crowding the neighboring display.',
],atmosphere=[
    'The displays reward a slow look, leaving the ordinary floor free for moving between subjects.',
    'The restrained surroundings give the collection an unusual presence, each small object set against a generous quiet.',
    'The gallery keeps a measured distance between the objects and their audience, close enough for details to matter.',
    'The room feels assembled around attention: a label, a shape, then a little space before the next thing.',
])
related('showroom','shop',[
    'Staged furniture settings occupy the {side} floor beneath a broad panel of {surface}.',
    'A display arrangement fills a shallow recess on the {side} side, framed in {surface}.',
    'The {side} demonstration bays are separated by low dividers faced in {surface}.',
    'A carefully coordinated furniture grouping gives the {side} end the appearance of a room within the showroom.',
],atmosphere=[
    'The furniture is arranged in carefully measured groups, each separated by a broad aisle and a change of color.',
    'The staged interior has the polished incompleteness of a home waiting for ordinary life to disturb the display.',
    'Small changes between the settings give the showroom a series of different domestic possibilities.',
    'The room presents furniture as an arrangement of choices, leaving the visitor free to move among them.',
])
related('studio','office',[
    'A compact {workstation} faces the {side} working surface beneath a panel of {surface}.',
    'The {side} equipment positions gather around the {workstation}, with fitted trim of {surface} keeping the edges close.',
    'A shallow recess of {surface} shelters the {workstation} from the broader {side} floor.',
    'The {workstation} sits at an angle to the {side} fittings, bringing several working surfaces within reach.',
],detail=[
    'Cable channels follow the back of the fitted surfaces, turning at neat right angles around the equipment.',
    'A patch of textured wall covering breaks up the harder panels near the working position.',
    'Small labels sit beside the fixed controls, their narrow lettering arranged in repeated rows.',
    'A narrow shelf carries the outlines of equipment shifted between slightly different positions.',
    'The nearest surface has a softer insert beneath the most frequently handled part of the setup.',
    'The fitted panels leave deliberate gaps around the equipment, exposing the practical structure beneath the finish.',
])
related('laundry','kitchen',[
    'The {folding counter} follows the {side} wall beneath a band of washable {surface}.',
    'Laundry fixtures face the {folding counter} across the {side} half of the room.',
    'A shallow recess of {surface} contains the {folding counter} at the {side} end.',
    'The {side} fittings turn around the {folding counter}, leaving a clear working strip between the machines.',
],detail=[
    'Round machine fronts reflect the room in blunt, slightly distorted circles.',
    'Fine lint has caught along a recessed seam despite the otherwise washable finish.',
    'A narrow instruction panel sits above the fixtures, the lower edge dulled by repeated cleaning.',
    'The folding surface has a softly rounded front lip that keeps fabric from catching on a sharp edge.',
    'A drainage channel follows the lowest part of the floor before disappearing beneath the fitted machinery.',
],atmosphere=[
    'Detergent gives the room a powdery sweetness, with the broad counter making an ordinary chore sociable.',
    'The practical arrangement leaves a comfortable edge for company while the laundry occupies the harder fittings.',
    'The room has a clean, domestic smell and the repeated geometry of work done one load at a time.',
    'The fixtures keep close to the walls, their pale surfaces repeating in the narrow sheen of the washed floor.',
])
related('changing','foyer',[
    'A narrow {bench} runs beside the {side} changing fittings beneath a band of {surface}.',
    'The {side} storage compartments face a simple {bench} across a modest patch of clear floor.',
    'A low return faced in {surface} shelters the {bench} at the {side} end of the changing space.',
    'The {bench} occupies a shallow recess on the {side} side, leaving the central changing floor unobstructed.',
],detail=[
    'Small hooks repeat along the wall, their rounded ends projecting just far enough to hold clothing.',
    'The storage fronts have narrow ventilation slots that make a darker pattern near the top.',
    'A simple mirror is mounted low enough to take in more than a face.',
    'The nearest floor has a fine grip texture, interrupted by a smoother strip beneath the bench.',
    'A shallow shelf leaves room for folded clothing above the more practical lower fittings.',
],atmosphere=[
    'A faint fabric smell lingers in the close air, and the clear floor leaves room for the awkward movements of changing.',
    'The bench has a softer shine along the front edge, where countless changes of clothes have worn away the sharper finish.',
    'The compartmented surroundings give the space a practical privacy, distinct from the rooms used for arriving fully dressed.',
    'The room is built around temporary arrangements: a coat put aside, a seat taken briefly, a clear patch of floor.',
])
related('recreation','hall',[
    'The {side} playing space is framed by a broad strip of {surface}, keeping the central activity area clear.',
    'The {side} boundary steps back around a shallow recess, giving this portion of the recreation floor a broader margin.',
    'A low structural edge of {surface} separates the {side} activity space from the surrounding passage.',
    'The {side} fittings follow the lines of the playing surface, turning the room\'s proportions toward the activity.',
],detail=[
    'Repeated movement has left arcs rather than straight tracks across the busiest part of the surface.',
    'The boundary markings change direction around a neatly fitted corner.',
    'The nearest wall has a more forgiving finish below shoulder height than the plain surface above.',
    'A broad panel presents a simple diagram of the activity, with the surrounding finish kept spare.',
    'The floor changes texture just beyond the main playing surface, making the limit apparent underfoot.',
],atmosphere=[
    'The clear central space carries broad, overlapping scuffs, a faded record of movements repeated in different directions.',
    'The arrangement makes movement legible, with the strongest lines following the repeated paths of play.',
    'The room has the practical wear of effort repeated for enjoyment as much as discipline.',
    'The open floor gives small gestures room to become visible, while the surroundings keep their supporting role.',
])
related('performance','recreation',[
    'The {side} performance surface lies beneath a broad decorative panel of {surface}.',
    'A change in floor finish defines the {side} edge of the performance space without enclosing it.',
    'The {side} wall recedes slightly from the performance floor, leaving movement room to carry.',
    'A low structural lip faced in {surface} traces the {side} boundary of the open performance surface.',
])
related('theatre','hall',[
    'Rows of {audience seats} face the {side} presentation space beneath a broad panel of {surface}.',
    'The {side} seating curves gently around the {audience seats}, bringing the presentation into a shared line of sight.',
    'A low partition of {surface} frames the {audience seats} on the {side} side of the room.',
    'The {side} ceiling steps upward above the {audience seats}, giving the presentation space a broader apparent scale.',
],atmosphere=[
    'The seating gives the room a quiet expectation, arranging an audience before anything has begun.',
    'Fabric dulls the small sounds of settling in, while the open presentation space keeps the room\'s attention.',
    'The room makes a shared view out of many individual seats, each one turned toward the same clear focus.',
    'Even in a pause between presentations, the arrangement suggests the particular hush of people waiting to watch.',
])
related('spa','living',[
    'A padded {chaise} rests beside the {side} wall beneath a muted panel of {surface}.',
    'The {side} treatment corner gathers around a low {chaise}, with softer finishes framing the surrounding {surface}.',
    'A shallow alcove of {surface} shelters the {chaise} from the more exposed {side} floor.',
    'The {chaise} stands a little away from the {side} wall, leaving the treatment position clear on either side.',
],atmosphere=[
    'Clean fabric and a faint scented preparation soften the room, lending the treatment space a deliberately unhurried character.',
    'The padded furniture gives the room a quieter scale than the practical fittings around it.',
    'The arrangement leaves room to settle without making the working part of the treatment space feel crowded.',
    'The muted finishes keep attention close, on the texture of fabric and the comfortable curve of a resting surface.',
])
related('pool','bathroom',[
    'The basin curves toward the {side} wall beneath a broad finish of {surface}.',
    'A hard rim traces the {side} water, separating the basin from a narrow band of {surface}.',
    'The {side} pool boundary steps inward, making a small change in the shape of the surrounding water.',
    'A broad panel of {surface} faces the {side} basin, reflected in fragments across the water.',
],detail=[
    'Pale deposits mark the line where small splashes have repeatedly dried against the hard edge.',
    'The basin lining is divided into a fine grid, the pattern softened by the water above it.',
    'A narrow drainage groove follows the rim before turning beneath the surrounding surface.',
    'The water breaks nearby reflections into overlapping shapes, keeping the harder geometry from looking entirely still.',
    'The submerged surface changes tone where the basin begins to deepen.',
],atmosphere=[
    'The water gives the enclosure a softer depth, while the washable surfaces return sound with a clear, hollow edge.',
    'The basin is the room\'s focus, leaving the surrounding ground to serve the simple business of moving beside it.',
    'A mineral damp hangs close to the water, making the harder finishes feel cool even at a distance.',
    'The repeated reflections add movement to the room without requiring any activity in the basin.',
])
related('airlock','office',[
    'The {side} panels fit closely around a compact compartment, their joins edged in {surface}.',
    'A shallow service recess interrupts the {side} enclosure beneath a broad panel of {surface}.',
    'The {side} wall curves slightly toward the floor, giving the fitted {surface} a close, contained shape.',
    'A thick framed panel occupies the {side} end, with {surface} following the sealed edges.',
],detail=[
    'Small fastenings sit in a precise line around the nearest access cover.',
    'The lower edge has a heavier seal than the panels above, making the compartment\'s divisions plainly visible.',
    'A narrow indicator plate lies flush with the surrounding finish, the engraved labels small and restrained.',
    'The floor has a fine raised texture for grip, with smooth channels at the edges.',
    'The fitted corners are rounded, leaving very little unused space between the panels.',
],atmosphere=[
    'The close-fitting enclosure has the clean, impersonal smell of seals, paint, and regularly wiped metal.',
    'Hard surfaces keep every small sound near, separating this brief transition space from the larger building.',
    'The close-fitting construction gives the room a precise, contained character.',
    'There is little room for ornament, only the repeated assurance of panels meeting where they should.',
])
related('bank','foyer',[
    'Substantial fittings define the {side} public edge beneath a restrained panel of {surface}.',
    'The {side} security boundary is built into a broad framed surface of {surface}.',
    'A deep recess breaks the {side} wall behind the formal public fittings.',
    'The {side} floor widens before a heavy dividing structure edged with {surface}.',
],atmosphere=[
    'The substantial fittings give ordinary business a ceremonial weight, with every boundary measured and neatly finished.',
    'The substantial fittings establish a guarded formality without filling the room with decorative distractions.',
    'The orderly surroundings keep the public position easy to read and the more protected spaces clearly separate.',
    'The room\'s weight lies in the fittings and boundaries, leaving the visible floor spare.',
])
related('roof','exterior',[
    'A raised roof seam follows the {side} margin beside a broad patch of {surface}.',
    'The {side} roofing steps around a low structural housing, the exposed finish interrupted by {surface}.',
    'A narrow drainage line crosses the {side} roof surface before disappearing beneath a raised edge.',
    'The {side} roof carries an older repair outlined by a slightly different tone of {surface}.',
],atmosphere=[
    'The exposed roof offers little enclosure, with the building\'s shelter lying beneath the visible surface.',
    'The upper structure gives the space a different scale from the rooms below, all seams, edges, and open air.',
    'The roof keeps a long history of exposure in pale stains and weather-rounded edges, above the shelter of the rooms below.',
    'There is no room-like ceiling here, only the exposed top of the building and the air around it.',
])
related('platform','exterior',[
    'The {side} platform edge rests above a visible support faced in {surface}.',
    'A broad span of {surface} carries the {side} footing, with the supporting joints exposed beneath the edge.',
    'The {side} structure narrows around a squared support, leaving the standing surface open to the surrounding air.',
    'A repeated line of {surface} traces the {side} boundary of the raised surface.',
],atmosphere=[
    'The open structure frames a place to pause without turning the platform into an enclosed room.',
    'The visible supports keep the difference between this footing and ordinary ground apparent.',
    'The surrounding air remains part of the space, with the nearest structure providing scale rather than enclosure.',
    'There is little to furnish here; the raised span and the view beyond it give the place a sufficient character.',
])
related('shore','exterior',[
    'A low ridge of sand follows the {side} shore, broken by a scattered band of {surface}.',
    'The {side} ground slopes through coarse grains toward a shallow pocket of {surface}.',
    'A narrow line of {surface} interrupts the {side} sand, separating finer grains from the rougher shore.',
    'The {side} beach gathers into a low hollow where {surface} has collected among the sand.',
],detail=[
    'Shell fragments lie with their curved faces turned at different angles, pale against the surrounding grains.',
    'Older impressions have softened at the edges until they look like small changes in the surface rather than tracks.',
    'A piece of weathered driftwood lies low in the sand, the exposed grain raised into narrow ridges.',
    'Fine grains have settled into the sheltered side of a small stone, making a delicate fan.',
    'A faint band of darker material marks where the shore has gathered a different mixture of debris.',
],atmosphere=[
    'The exposed shore has little enclosure, leaving the interest in small textures close to the ground.',
    'Salt lingers faintly over the sand, and the yielding surface keeps no mark quite as firmly as it first appears.',
    'The shore is made of countless small edges worn soft, each one a little different from the next.',
    'The open ground has a quiet instability, a surface always capable of settling into a slightly different shape.',
])
related('channel','underground',[
    'The water channel follows the {side} masonry, where {surface} marks a change in the retaining wall.',
    'A low ledge of {surface} projects into the {side} channel above the darker water.',
    'The {side} channel wall thickens around a blunt structural pier, narrowing the visible water beside it.',
    'A shallow inlet interrupts the {side} masonry, the water carrying the outline past a seam of {surface}.',
],detail=[
    'Silt forms a dark crescent behind the nearest projection, finer than the grit along the exposed edges.',
    'A pale mineral line follows the wall above the water, rising and falling with older imperfections in the masonry.',
    'Small disturbances divide the confined surface into short overlapping ripples.',
    'The lower stone has a darker, smoother skin than the drier material above.',
    'A repaired joint has changed the outline of the wall just enough to catch a narrow pocket of debris.',
],atmosphere=[
    'The enclosed water gives the passage a cool, mineral damp, with the masonry keeping the visible reach close.',
    'This section belongs to the channel itself; the harder margins show where water and built structure repeatedly meet.',
    'The confined surface returns broken reflections from the nearest stone, making the channel seem deeper than the visible bottom.',
    'The channel draws the eye into the deeper enclosure, where the pale waterline fades against darker masonry.',
])
related('camp','living',[
    'Fabric screens meet around a rough support at the {side} edge, enclosing a modest camp interior.',
    'The {side} shelter slopes toward a stout supporting frame, with a lower skirt close to the ground.',
    'A doubled layer of fabric gives the {side} shelter a heavier edge than the broader enclosure.',
    'The {side} camp structure is divided by a simple hanging screen, leaving the central floor clear.',
],detail=[
    'The fabric keeps broad creases from earlier folds, crossing the seams at different angles.',
    'A fastening has been wrapped several times around the nearest support, leaving a compact knot against the rough material.',
    'The ground is firmer through the middle than beneath the lower shelter edges.',
    'A patched section uses a slightly different weave, apparent where the two materials overlap.',
    'The lower seam curves around a small irregularity in the frame rather than meeting it squarely.',
],atmosphere=[
    'Canvas and earth lend the shelter a close, temporary intimacy.',
    'The camp smells of canvas and dry earth, the close fabric giving small sounds a soft, temporary shelter.',
    'The simple enclosure makes every small adjustment of fabric and frame visible.',
    'The shelter offers a human-sized pause within a larger setting, held together by ordinary practical choices.',
])
related('vessel','vehicle',[
    'Ribbed bulkheads frame the {side} passenger space, with {surface} tracing the inset panels.',
    'The {side} compartment narrows around a broad structural rib faced in {surface}.',
    'A fitted recess interrupts the {side} bulkhead, exposing the layered construction beneath the {surface}.',
    'The {side} shell curves close above the passenger space, leaving little unused room between the fitted surfaces.',
],atmosphere=[
    'The compartment carries the close smell of enclosed travel, with every fitting shaped around the larger craft.',
    'The repeating ribs make the structure feel near even where the passage remains clear.',
    'The interior has a practical compactness, turning the needs of the vessel into the proportions of the room.',
    'The fitted surfaces give the space a sheltered, slightly impersonal character familiar to shared journeys.',
])
