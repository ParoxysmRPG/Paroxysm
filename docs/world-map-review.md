# World map repairs and market-door review

The earlier repair pass changed 71 room records across seven area files. The
continued audit changed another 765 existing room records and removed 27
unreferenced duplicate rooms. Details and the limits of the checks follow below.
The engine's active **The Crossroads** definition of room 302600 remains; its
obsolete first definition was removed in the earlier pass.

## Confirmed repairs retained

| Location | Repair |
| --- | --- |
| Black Rose Book Store | Bathroom 16519 east of nonfiction 16514; occult section 16520 east of cafe 1836; office 16521 through the existing northeast cafe door. |
| Howl at the Moon | Den 16546 through the lounge's north door, from 16547. |
| The Retreat | Cafe 2158 up to clothing section 7390, with return stairs intact. |
| Gravesend Hardware | Bathroom 16645 west to alley 16658; both sides have the door. |
| Town Hall | Cafe 15093 south of front lobby 18438. |
| Petite Cuisine | Garden 2527 south of dining room 16796; garden uses outdoor park terrain. |
| Tijuana | Abandoned shop 34006 through the strip mall's southeast door, from 34001. |
| Rooftops | 9103, 9104, 2998, 7273, 36028, and 36037 use roof terrain without indoor/bedroom flags. Fourteen other town roofs meet the air above them consistently. |
| Apartment 101 | Existing concealed office/bedroom door between 16697 and 16680 works from both sides. |

Thirty-three forest-side exits now respect the corresponding walls/windows of
town buildings. Other asymmetric building boundaries were closed on the
previously passable side, including coastal room 151817. Existing arena entry
doors remain the route into the arena; its two wall bypasses were closed.

## Continued world audit

| Finding | Repair |
| --- | --- |
| 477 underground caverns copied their surface room's identity | Replaced street/park names, descriptions, and copied seating places with cavern descriptions. Terrain, coordinates, features, and exits are preserved. |
| 241 solid roofs were named Sky or Skies | Added rooftop names and descriptions consistent with their existing roof terrain. |
| Six solid upper floors were named Sky or Skies | Added upper-floor names and descriptions, preserving their existing terrain and access. |
| 29 town rooms had empty names | Named them according to their existing room, commercial, park, or roof terrain. |
| Four upward exits reached the wrong coordinates | Corrected 131622 up to 9775, 131734 up to 9601, 197697 up to 114108, and 197699 up to 114106. Each destination already had the matching downward exit. |
| 27 unused records duplicated connected world coordinates | Removed room 1842, fourteen forest boundary copies, and twelve ocean copies. None had incoming exits or saved room references. Coordinate lookup now selects the connected room, including Ash/Paine intersection 15215 and Gravesend Bay 3112. |
| Three sky rooms had no return route to town | Opened the obstructed downward returns from 9313 and 3879; this also restores the route back from 3497. |
| Eight further roof boundaries disagreed | Restored six downward air-to-roof returns and closed two downward wall bypasses through roofs 5210 and 6868, where no stairs exist below. |

`map-identity-repairs.json` and `map-egress-repairs.json` record this continued
pass. The repair scripts are dry runs by default and report no further changes
when run against the repaired data. No general door normalization was added.

## Correction: goblin market doors

Exit symmetry alone is **not evidence of a broken ordinary door**. The
`decorate marketdoor` command marks a brick wall as a market slot.
`market_link()` changes its destination at runtime, and its return direction
comes from property data rather than the opposite compass direction.

Museum auditorium **14817 south** and cafe **14808 north** are confirmed market
slots. Their speculative static repairs have been withdrawn. Their original
saved destinations, door flags, and resets are retained. The gift shop remains
accessible through its existing ordinary routes.

The saved property file contains 46 configured market slots, all in town. Six
additional forest-facing destinations are still referenced by the goblin market
but have no corresponding return direction in that property file. This missing
metadata also prevents confidently classifying historic forest doors.

After this review, **211 speculative exit edits were withdrawn**, including the
196 automatic return-door additions, six removals of doors into air, six added
forest return paths, and three edits to the named market connections. Their
associated reset changes were restored. These changes must not be reapplied
without establishing the purpose of each door.

The audit excludes all configured market slots, including inactive brick
walls, and all eight external market exits from ordinary symmetry checks. It
labels unclassified door mismatches as candidates that may be market doors.
The explicit repair recipe performs no general door normalization.

## Remaining candidates and verification

The final scan loads **96,424 rooms**. Exit record validation, missing exit
destinations, door-reset references, duplicate IDs and world-grid coordinates,
reviewed terrain/name mismatches, and coordinate errors supported by matching
return exits have **zero findings**. The separate institute audit checks 1,399
rooms and also has zero findings.

The directed reachability check covers **71,951 rooms reachable from town**,
allowing doors and traversal skills while respecting walls. Only well room
2044 lacks an exit route back. Its falling entrance and confinement flags make
it a suspected hazard requiring design review; the audit does not invent a
ladder. This graph check does not prove that every route is usable by every
character or that every lock has an obtainable key.

There are **543 rooms with review candidates**, not 543 confirmed defects:
202 unclassified door mismatches, 31 asymmetric structural boundaries, 320
sealed interiors, two market connections, two roof-name exceptions, and the
well (categories can overlap). These include disconnected travel/dream/test
rooms, sealed lots, creation/void exits, and unusual realm-edge links. The
indoor landing 2664 and rooftop apartment 2999 are roof-name false positives.
Legacy forest indoor flags and nonadjacent realm/ocean connections also lack
enough evidence for automatic reconstruction. The audit does not invent
entrances or rewrite runtime-managed market routes.

Run the read-only audit with:

```text
py tools/audit_world_map.py --report docs/world-map-candidates.json
py tools/audit_institute.py --report docs/institute-map-audit.json
```

`world-map-repairs.json` contains the earlier retained changes;
`world-map-withdrawn-changes.json` records the withdrawn edits. The disposable
world integration test exercises movement through restored ordinary rooms,
wall collisions, terrain, underground travel, coordinate lookup, the four
vertical corrections, flight out of the three former sky traps, the unique
Crossroads definition, and preservation of market slots and unclassified
forest doors. All 211 withdrawn exit changes were checked against their
original data and remain withdrawn. Dorm, school, institute, and world-map
integration suites all pass against the final area data in a disposable server
copy. The fixture reports its existing missing `player/GroundObjects` warning.

Area changes require reloading the affected data or restarting the running
server before they appear in play.
