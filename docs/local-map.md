# Local maps

Ordinary `look`, automatic room looks after movement, and directional looks show
a compact coloured map beside the room title, with room text flowing beside
it and then below it. Looking at objects or characters does not add a map.
`map` shows a larger local view outside combat; during combat it retains the
tactical map. `map local` explicitly requests the surrounding rooms and
`map combat` requests the existing tactical view. Local maps add no
command delay. `help map`, `map key` and `map legend` explain the symbols;
`help minimap` links to that guide.

`map off` hides the map in look, `map on` restores it, and `map toggle` switches
the preference. It is stored in the existing saved `Comm` flags as
`COMM_NOMINIMAP`; existing characters default to enabled. Manual local and
combat maps are independent of this preference. Turning it off bypasses the
renderer entirely during look.

The minimap is a 13-column, 7-line frame around a 3-by-3 room grid. It shares
the title's first line. Its right edge uses the main description's actual
display width, capped by the player's configured width, so prewrapped room
descriptions and wider clients do not leave the map protruding to the right.
Room-status text and description begin directly beneath the title in the left
column. The description resumes at full width below the seven map rows.
Authored single line breaks reflow; paragraph breaks remain. Color codes stay
intact across wraps. Descriptions narrower than 30 columns omit the look map.
All map borders use the same basic green (`` `g ``) as the written direction
brackets.

Maps are north-up and show the current floor. They shrink to the character's
configured screen width. Rooms use terrain/building symbols, with the player
marked `@`; connectors distinguish entrances, doors, windows and movement
requirements. On the larger map, ordinary connections at the edge continue
beyond the viewport; the compact map shows connections within its smaller grid.
Nonlocal connections, other-floor connections and conflicting placements use
`!` instead of inventing a room position. The output uses existing basic colour
codes and ASCII glyphs, so its layout also works with colour disabled.

The map follows actual exits. It uses coordinate differences to reject distant
or contradictory geometry; same-area rooms with shared legacy coordinates use
directional layout with collision checks. It does not search for disconnected
rooms nearby. Hidden exits, magically hidden exits, invisible rooms and solid
walls are filtered; administrators retain the existing hidden-exit visibility
override. Closed opaque doors and glass boundaries stop expansion. Live door
flags are read on each request. Cross-world routes are left to the normal exits
display. Local maps share the ordinary look sight restrictions and are omitted
in dreams and the deep Nightmare.

Up/down marks require an ordinary vertical connection: no jump, climb or fall
requirement, and neither endpoint may be aerial or aquatic terrain. The rule
does not depend on the viewer's flight/jump abilities. Outdoor forest-to-forest
vertical links are also excluded because legacy canopy rooms still carry
forest terrain and zero movement requirements. This conservative exception may
omit an outdoor forest stairway without distinct metadata; indoor stairs are
preserved. The map does not change any room or movement data.

## Cost and implementation

`src/local_map.cc` is a shared renderer with fixed local arrays for the queue,
canvas and per-request visibility lookup. It visits at most 9 rooms / 90 exit
slots for the 3-by-3 minimap, or 165 rooms / 1,650 exit slots for the 15-by-11
larger map. Smaller terminal widths reduce the horizontal limits. Each visited
room is processed once. Visibility decisions are reused for destinations
encountered through multiple exits, including denied rooms.

The renderer performs no world-grid rebuild, coordinate-index search, property
classification scan, character/item listing or pathfinding. The existing
`can_see_room` access predicate remains in use; special-area checks can inspect
the viewer's access items. Current-room darkness checks stay at the command
boundary rather than running expensive lighting calculations per map tile.
Room prose is collected once. Layout adds linear text-width measurement and
reflow, with no extra room scans. The first seven rows are sent together and
the remaining prose uses the existing pager. The output pipeline handles
colour and socket buffering. No
persistent map cache needs invalidation after door, room or builder changes.

## Verification

Run from Linux/WSL:

```sh
make -C src -j4
python3 tools/run_local_map_integration.py
python3 tools/run_local_map_integration.py --sanitize
python3 tools/test_look_optimization.py
python3 tools/run_local_map_world.py
```

Focused tests compile the production renderer and command against instrumented
visibility fixtures. They cover secret exits, walls, door freshness and interior
privacy, vertical-route exclusions, canopy exceptions, coordinate conflicts,
diagonals, narrow displays, colour, command routing and bounded traversal.
Increasing a cyclic fixture from 289 to 2,401 rooms leaves output and operation
counts unchanged. The renderer fixture reports timing with controlled visibility
helpers; this is a renderer microbenchmark, not live server latency or throughput.

The world test boots a disposable copy, checks actual town/academy/cavern/roof
maps, known canopy rooms, title/map placement, narrow and long colored titles,
look/map/help integration, sight restrictions and save/load of the preference. It
also emits map samples for layout review. No production world is booted or
modified by these tests. Restart/copyover is needed to load the rebuilt engine
and updated helpfile in a running game.
