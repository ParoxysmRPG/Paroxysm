# Combat map rendering

`map` during combat and `map combat` show the tactical map. `map local` retains
the surrounding-room view. `help combat map` contains the tactical colour and
symbol key; `map key`, `map help` and `map legend` select that guide in combat.
The existing three-second command delay remains unchanged.

The grid is north-up, shows the viewer's facing and retains the nonlinear
distance scale and forward terrain cone. Facing crops whole two-character
cells, including diagonal headings. Maps fit the configured terminal width
and never exceed 31-by-31 cells. A green frame and short help hint surround the
map; the symbol legend lives in the helpfile.

`Me` is white, the current visible opponent is magenta, aggression-based
hostility remains red, and other visible characters remain green. The current
opponent is `cfighting`, falling back to `chattacking` for a pending attack;
the damage-history `target` fields are not used. When actors overlap, the
viewer wins, then that visible opponent, then other characters, then cover.
Ties retain the original character order.
Capture/extraction markers use gold `CC`/`EE`. An objective covered by the
viewer or their opponent is also identified beside that actor in the roster.

Labels remain exactly two ASCII columns. Unique name prefixes are retained;
collisions receive short IDs, reserving `Me`, `CC` and `EE`. IDs match the
roster and may change when visible characters change. If the finite two-column
namespace is exhausted, excess entries use `??`; the roster still includes
them. These are display labels, not new combat-command targeting aliases.

Visible cover uses a cyan `[]` marker and turrets use `{}`. Both symbols are
reserved from ordinary actor labels, and take the usual target/aggression
colors when applicable. The roster identifies cover and turret types and
retains each object's name and coordinates when the map cell is occupied.
Protected actors retain their colored identity marker with an underline;
their roster entry names the visible cover. Cover elsewhere in the same
coarse map cell is noted separately, without claiming protection.
Underline tags now render correctly as ANSI SGR 4/24 or existing MXP tags,
and disappear without changing cell width when color is disabled.

Cover status follows the existing position rule: a visible NPC with
`ACT_COVER` in the same room, within one local coordinate on each axis.
`ACT_TURRET` alone does not grant cover; cover and turret actors do not take
cover themselves. Only objects already admitted to the viewer's snapshot
participate, so the annotations do not expose hidden objects or occupants.
The snapshot builds a coordinate lookup with at most nine entries per cover
object, then performs one lookup per eligible actor. It does not call the
room-scanning cover helpers separately for every character. Names and
visibility results are reused, and the lookup is discarded after each draw.

## Work shared within one draw

`src/combat_map.cc` builds one viewer-specific snapshot using the existing
`can_see_char_distance` and `can_map_see` predicates. Positions, distances,
visible names and labels are reused by placement and the roster. Visible
bystanders and combat objects remain included. The separate automatic-size
calculation now walks the existing active-fighter index instead of every
character in the world and computes each candidate's distance once.

The roster uses dynamic storage and a stable distance sort. This removes the
old 100-entry array overflow and quadratic sorting. Overlap counts belong to
the snapshot; drawing and scanning no longer read or write the legacy
character-global `mapcount`. This prevents counts from leaking between draws
or viewers. `battleflags` uses bounded reusable storage rather than leaking
an allocated string for every fighting character on every scan.

`CombatMapTerrain` in `src/fight.c` caches room visibility, reachability, light
and final terrain within a draw. Coordinate resolution also caches failures
and includes the source room in its key, preserving route-dependent lookup
behaviour. Axis positions are computed once, and each two-character cell is
processed once. Repeated terrain colours emit only one colour transition per
run. All caches are discarded after the draw, so door, movement, concealment
and lighting changes are visible on the next request.

Map reachability uses the same movement/path checks as before, through a
quiet wrapper that suppresses repeated movement-warning text. Ordinary
movement retains that text. The shared `ordinary_map_vertical_route` helper
excludes jump, climb, fall, air, water and ambiguous outdoor canopy routes.
Combat vertical markers also require visible, open exits and a reachable
destination; a mere upward exit no longer creates an unconditional `^`.

## Verification

Run from Linux/WSL:

```sh
make -C src -j4
python3 tools/run_combat_map_tests.py
python3 tools/run_combat_map_tests.py --sanitize
python3 tools/test_operation_render_launch.py
python3 tools/run_local_map_integration.py --sanitize
python3 tools/test_combat_commands.py
python3 tools/run_local_map_world.py
```

Focused tests compile the production snapshot and extract the actual map,
roster, visibility and objective functions against instrumented fixtures.
They cover 0, 99, 100, 101 and 350 visible actors, label collisions and short
names, long roster names, fresh counts, player/opponent priority, objective
overlap, all eight compass headings, narrow displays, exact cell boundaries,
stairs, smoke, landmines, cloak blindness, invisibility, ghosts and stasis.
Cover cases compare against the production proximity predicate, including
diagonal adjacency, room/floor boundaries, turret roles, hidden cover,
movement freshness, overlapping cells and retained objective markers.
The disposable-world suite also checks actual ANSI/MXP/no-color rendering,
visible-width measurement, a production cover prototype and the helpfile.

One synthetic 31-cell terrain fixture has 1,488 terrain columns but only 140
distinct reachability and lighting checks per draw: 90.6% fewer reachability
checks than recalculating per column. Snapshot filtering runs once per
candidate and the roster does not repeat it. These are measured operation
counts, not a live-server latency or throughput claim.

The existing operation signup/launch assertions remain in their regression
suite; rendering checks moved to the dedicated combat-map suite because the
new presentation intentionally differs from the old bytes. The disposable
world test exercises both map modes, actual target labels, loaded helpfiles,
look integration, command delay and fresh overlap counts without starting or
changing the live world. A restart/copyover loads the rebuilt engine and help.
