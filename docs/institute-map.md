# Institute map audit

The Student Dormitory Nexus (3347) is an indoor house room at `(5, 60, 1)`.
Directly below it, the Student Dormitory Entrance (16156) is an indoor house
room at `(5, 60, 0)`. The entrance has solid walls, an eastern connection to
the covered walkway, and stairs up to the nexus. Neither room uses grassy-field
or water terrain. These details are verified after loading the saved world in
the engine. Restart the live server to load the changes.

The institute audit covers 1,399 rooms within its coordinate bounds, including
the campus, clinic, college houses, dormitories, grounds, roofs, and basements.
It checks named roof terrain and flags, sealed interiors, ordinary passages
through structural boundaries, door pairs, room destinations across loaded
areas, and the identities of all 24 assigned college-house bedrooms.

## Repairs

This pass changes 298 existing room records. Room vnums and coordinates stay
the same. A room-by-room record is in [institute-map-repairs.json](institute-map-repairs.json).

- Corrected 133 named roofs and walkway canopies using air, forest, or indoor
  terrain, plus three other roofs with incorrect indoor or bedroom flags.
  Clinic roofs now describe roofing and ventilation instead of clinical
  waiting areas; the misplaced waiting-chair places were removed.
- Resolved 42 ordinary one-way structural boundaries. Most were openings
  through walls or floors, including routes from lawns into upstairs bedrooms.
  Those now agree with the solid boundary on the other side. The biodome's
  southern airlock entrance, jungle-gym ladder, and Rook rooftop hatch are
  usable connections with matching return routes.
- Reopened eight sealed college-house rooms as studies, sitting rooms, or
  pantries. The isolated sheriff stair room has no basement beneath it; it is
  now a supply room reached from the department hallway.
- Enclosed the xeno-pharmacology office, gave it a proper western entrance and
  a roof, and corrected its park terrain. Corrected the remaining three
  waterlogged fields beside the dormitories, the outdoor flag on a clinic
  corridor, and stray bedroom flags on outdoor rooms.
- Matched all 24 college-house bedroom names to their assigned room numbers.
  Purity 6 was incorrectly labeled as a hallway; Purity 4 lacked its bedroom
  flag. The existing room IDs and assignment slots remain stable.
- Corrected the college-house key and decoration checks to compare against
  `dorm_room(ch)`. They previously compared a room vnum against the boolean
  result of `room_in_school`, preventing assigned residents from using their
  own locked bedrooms.

The pool retains its shallow, deep-water, and underwater rooms. The air above
the enclosed biodome canopy remains indoor air. Existing clinic and sheriff
locks retain their saved reset states except where a specifically repaired
door or boundary required matching sides.

## Verification

```sh
python3 tools/audit_institute.py --report docs/institute-map-audit.json
make -C src -j4
python3 tools/run_institute_integration.py
python3 tools/run_dorm_integration.py
python3 tools/run_school_integration.py
```

The final structural audit reports zero findings in its checked categories.
The before/after reports are [institute-map-audit-before.json](institute-map-audit-before.json)
and [institute-map-audit.json](institute-map-audit.json).

The build and all three engine suites pass. Tests use disposable world copies
and ordinary students to exercise assigned-room keys, outsider rejection,
leaving bedrooms, decoration eligibility, repaired passages, nexus floors,
the existing 20 student dorm rentals, and the uniform shop's twenty purchases.
All 120 authored descriptions pass prose-length, color, and place-keyword checks.
