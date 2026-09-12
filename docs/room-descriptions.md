# World descriptions

All 96,553 rooms in the shipped top-level `area/*.are` files now have finished
descriptions. This includes all 96,452 rooms loaded by `area/area.lst` and the
101 rooms in the unlisted legacy `aust.are`. Historical backup directories and
temporary files are outside the runtime world and were left alone.

There are 719 distinct descriptions and 2,576 saved places. Similar terrain
shares prose; named landmarks and important interiors use authored entries,
with building and subarea details where appropriate. Room names, flags,
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
is saved as `B 1` in the room record and restored by the area loader. The 9,207
finished non-terrain definitions carry this same ownership flag. Reusable
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

The authored catalogue lives in `tools/room_catalogue.py`,
`tools/room_landmarks.py`, and `tools/room_interiors.py`. Regenerate the checked-in
C++ default header after changing terrain or transit prose:

```sh
python3 tools/generate_room_defaults.py
```

## Verification

The final audit reports zero blank, placeholder, or undersized descriptions,
zero colour errors, and zero invalid or ambiguous place records. Rerunning
the migration left every area file byte-for-byte unchanged.

```sh
python3 tools/describe_world.py --check
make -C src -j4
python3 tools/run_room_integration.py
```

The build and engine integration checks passed under Ubuntu/WSL. The engine
test boots a disposable copy of the world without starting the game loop or
opening a server socket. It loaded 96,452 rooms and 2,576 places and checked
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
The provided tutorial describes a newer Haven setting and some newer systems:
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
