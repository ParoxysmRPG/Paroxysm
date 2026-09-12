# World descriptions

All 96,553 rooms in the shipped top-level `area/*.are` files now have finished
descriptions. This includes all 96,452 rooms loaded by `area/area.lst` and the
101 rooms in the unlisted legacy `aust.are`. Historical backup directories and
temporary files are outside the runtime world and were left alone.

There are 5,408 distinct descriptions and 2,070 saved places. All 5,137 rooms
covered by the interior catalogue have distinct descriptions after ignoring
colour, capitalization, and whitespace. Similar outdoor terrain shares prose;
landmarks and interiors use authored entries, with building and subarea details
where appropriate. Room names, flags,
coordinates, exits, resets, and existing feature data are preserved. The
migration asserts a structural checksum before writing each area.

Descriptions use the ordinary room description field edited by `Decorate
description`. Seating, counters, and other gathering places use the existing
`P` records edited by `Decorate place`, so players can discover their keywords
in the description and use `join`. These places are positions for characters;
they do not create inventory items, containers, or services. Colour highlights
use supported single-character codes and finish with a reset.

## Decorate precedence

`Decorate` edits mark the room as owned by the decorator. This includes name,
description, nightmare description, place edits, and place deletion. The flag
is saved as `B 1` in the room record and restored by the area loader. The 10,306
finished definitions carry this same ownership flag. Reusable
transit rooms remain automatic until someone decorates them.

Automatic description generation and procedural resets respect this flag.
Even text identical to an automatic default remains protected, and deleting
the last place does not cause automatic places to reappear. The migration also
skips owned records. Ordinary authored text without a flag is preserved by the
default-filling helper and the migration.

An empty description can receive a display/save fallback without modifying an
owned editor buffer. This prevents an unfinished editing session from saving
a blank description while keeping the decorator's active work intact.

## Procedural rooms

`src/room_descriptions.c` supplies finished defaults for all 33 terrain types,
the four realm forests, and transit contexts. Creation, loading, rendering,
travel, and procedural reset paths use the shared helpers. Changing an
automatic transit room back to a sidewalk removes its automatic vehicle
places; custom places are preserved. Room copies deep-copy their place lists.

The shared catalogue lives in `tools/room_catalogue.py`,
`tools/room_landmarks.py`, and `tools/room_interiors.py`. Individual interiors
live in `tools/indoor-room-descriptions.json`. Regenerate the checked-in C++
default header after changing terrain or transit prose:

```sh
python3 tools/generate_room_defaults.py
```

## Verification

The final audit reports zero blank, placeholder, or undersized descriptions,
zero colour errors, zero duplicate interior descriptions, and zero invalid or
ambiguous place records. The interior application is a no-op when repeated.
A disposable ordinary migration preserves all descriptions and place text;
it normalizes one record's place ordering, then becomes byte-for-byte stable.

```sh
python3 tools/describe_world.py --check
make -C src -j4
python3 tools/run_room_integration.py
```

The build and engine integration checks passed under Ubuntu/WSL. The engine
test boots a disposable copy of the world without starting the game loop or
opening a server socket. It loads 96,452 rooms and checks
all terrain defaults, stock recognition after loading, colour conversion,
whitespace recovery, and repeated default application. It also exercised the
real `Decorate` command and string editor, joining/deleting places, persisted
decoration ownership, deep copies, procedural resets, and subway-to-sidewalk
transitions. Existing compiler and world startup warnings remain in the logs.

Machine-readable results are in `room-description-audit.json`; build and
engine output are in `room-description-build.log` and
`room-description-integration.log`. `tools/describe_world.py --write --check`
applies catalogue defaults only where editorial ownership permits it.

## Newbie school restoration

The twelve lessons in `limbo.are` now use the user's supplied tutorial text,
with paragraph breaks preserved. `tools/newbie_school.py` holds their source
by vnum; the catalogue handles these before general room descriptions.
The titles at 62, 59, and 53 are now Concept and Character, Setting, and
Organizations respectively. Their existing north/south route is unchanged.
The transcript's HTML spaces, command echoes, lighting, weather, exit displays,
and pager prompts are not embedded in room prose. Minor typos were corrected,
and the pager-truncated Setting paragraph has a completed final sentence.

The generic tutorial seating places were removed. Clothes and Tailoring (52)
has the supplied shower place, alongside its existing bathroom and stash
flags. Its existing shopkeeper (mobile 2) and all 25 stock resets are retained.
The shorts reset was moved to the end of that stock block so the engine's
inventory order makes `buy 1` purchase white cotton shorts, as the lesson
instructs. Integration checks exercise `list`, the purchase as an ordinary
player, the resulting object vnum and payment, and `join shower`.

All twelve lessons retain `B 1`; later `Decorate` edits take precedence.
The provided tutorial describes a newer Paroxysm setting and some newer systems:
for example, this source tree has no `rpfight` command implementation. The
requested lesson wording is retained; restoring tutorial text does not add
those missing gameplay systems.

## Functional bathing places

194 bathroom, shower, and steam-room records now expose a `shower` place and
carry `ROOM_BATHROOM`. This replaces 178 basin places and 13 generic washing
areas, and corrects three bathrooms previously classified as a bedroom or a
well. Players can `join shower`; the existing `in_shower` check then enables
washing in the character update, removing blood and dirt and updating hygiene.
The bathroom flag also satisfies the property-room bathing restriction.

The catalogue uses shower keywords for these interiors. Bathroom titles take
precedence over generic room/bedroom matches, and `well-appointed` and
`well-stocked` no longer match the well rule. Room exits, identities, sectors,
and non-bathroom flags are preserved. The world description audit passes.

## Atmospheric prose refresh

The September 2026 editorial pass refreshes 95,903 saved room descriptions
across 31 area files. All 33 terrain defaults, four realm forests, and three
transit defaults now use richer sensory detail. Common interiors, establishment
themes, and landmarks such as the Lodge, Rosie's Diner, Arkwright Cemetery,
and the Dreamheart receive more distinctive prose. The revised text keeps
time of day, weather, and occupants available to the game's live systems.
New prose uses `it's` for `it is` and names the subject in possessive phrases.

The saved-world refresh matched the previous catalogue text, including older
wrapping and apostrophe variants, before applying new wording. It also
rephrased 339 existing place descriptions while retaining every place keyword.
Two transit cars carrying forest prose now describe their passenger interiors,
making their existing `seats` discoverable again. No room names, identities,
flags, ownership markers, coordinates, exits, resets, or tutorial records
changed. Ordinary migration and runtime decoration precedence remain intact.

The refreshed world passes the description audit with zero errors. The runtime
header matches the catalogue, and the release build and disposable engine
integration pass under WSL. The integration runner uses fresh release objects
from `src/.build-local/release-sanitize0`.

## Useful places

The place-quality pass removes 695 filler positions, including standing areas,
room centers, browsing aisles, and viewing areas. Ordinary floor space remains
part of the room description. A room does not need a place record unless there
is a useful, distinct destination for company to gather.

The 1,880 retained non-tutorial places now describe the furniture or feature
itself, with details such as upholstery, working surfaces, sightlines, and the
spacing of seats. Of these, 615 have clearer names: bedrooms expose `bed`,
lounges expose `sofa`, and reception seating becomes a `waiting bench`.
Classroom `front desk` and `rear desks` keywords remain unambiguous. Counters,
booths, benches, working tables, and bathing places retain their useful roles.
The tutorial shower and all twelve tutorial records remain unchanged.

The catalogue, saved area records, and automatic runtime places agree on the
revised furniture. The runtime recognizes the previous automatic place text
when updating or removing stock places; custom text and Decorate ownership
still take precedence. Engine checks exercise joining beds, sofas, booths,
and classroom desks, removal of empty-area places, legacy automatic places,
and functional showers. The description audit reports zero errors.

## Individual indoor descriptions

The interior pass covers 5,137 saved rooms, including all `ROOM_INDOORS`
records, legacy indoor sectors, and interiors identified by their names.
Some old flags describe roofs, woodland, or water; their prose retains the
actual setting. Outdoor approaches mentioning a building are excluded from
the additional name-based coverage. All 93 covered Mists rooms are distinct.

This pass changes 4,937 descriptions. Existing distinctive scenes and all
twelve tutorial records are preserved. The 91,416 records outside the scope
are unchanged, and a comparison against the starting world verifies that
names, flags, sectors, coordinates, exits, resets, and feature data remain
intact. Finished interiors acquire `B 1` where needed to survive resets;
reusable transit shells retain their automatic ownership policy.

Descriptions combine individually written landmarks with authored scene
details for repeated interiors. The latter vary their focal feature, finish,
layout, and atmosphere while retaining suitable building character. The saved
JSON contains the complete prose for each room; nothing is randomized during
play. New places refer to useful furniture or features. Corridors, empty
interiors, and open performance floors do not acquire generic standing areas.
Open-air bathrooms keep their showers, and the misplaced well rim in the
Mists bedroom is replaced by a bed.

`tools/indoor_rooms.py` defines coverage and lookup. `tools/indoor_scenes.py`
and `tools/indoor_landmarks.py` supply the initial authoring material.
`tools/author_indoor_rooms.py --draft` creates a catalogue only when none
exists. After reviewing edits to the saved JSON, apply them with:

```sh
python3 tools/author_indoor_rooms.py --apply
python3 tools/describe_world.py --check
```

Application checks all source records before writing any area file. Later
world edits cause a conflict rather than being overwritten. Reapplication
without catalogue edits changes no area files. The ordinary world migration
continues to respect decoration ownership.

Each of the 100 reusable vehicle slots has a distinct taxi default. The taxi
command selects that slot's text, so the 90 saved taxi descriptions remain
distinct after loading and during reuse. Automatic seat recognition tolerates
different line wrapping and removes those seats when the shell becomes a
sidewalk. Engine tests exercise saved and generated taxis, preservation of
individual interiors through resets, and the corrected bathing places.
