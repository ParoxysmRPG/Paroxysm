# Student dormitories

From the covered campus walkway (15641), go **west, up** to reach the Student
Dormitory Nexus (3347). The ground entrance is 16156. From the nexus, Queenson
is north, Kingson northwest, Bishop south, and Rook southwest. The laundry room
is west and the shared sitting room east.

Use `rent 1` through `rent 5` in a house's common room or upstairs landing.
Rental is free for college students; `rent` lists vacancies, `rent stop` ends a
rental, and `roomie <number>` claims an available roommate slot. A resident or
roommate can `open <direction>` to use their rental key. The bedroom doors start
closed and locked.

Each house entrance displays a resident roster with rooms 1 through 5, residents,
roommates, and vacancies. Use `look roster` to read it again. The ground entrance
and nexus display the complete directory for all four houses. Rosters read the
current rental records, so renting, leaving, and inactivity cleanup update them
immediately. Rental changes are saved immediately and survive a restart.

Each student can hold one dorm assignment, as either resident or roommate.
Inactive characters lose their assignment during the regular college update:
the existing college inactivity counter exceeds 500, or they have more than
seven full days of inactivity. Deleted characters and former students also lose
their assignments. Online students keep their rooms. If a resident leaves or is
removed, an active roommate takes over the rental; when both leave, the room
becomes vacant.

| House | Common room | Upstairs landing | Rooms 1–5 |
| --- | --- | --- | --- |
| Bishop | 3881 | 9023 | 3341, 9017, 9016, 9003, 9004 |
| Rook | 8996 | 9431 | 8997, 9005, 9001, 9006, 9014 |
| Queenson | 3894 | 3963 | 9049, 9050, 5951, 9037, 9038 |
| Kingson | 9032 | 9465 | 9035, 9034, 9033, 9036, 9042 |

Each house's first three rooms are reached from its common room, with rooms 4
and 5 upstairs. Rook has only room 1 downstairs; rooms 2–5 are upstairs. Its
landing has room 2 northwest, room 3 north, room 4 west, and room 5 south.

## Repairs

Queenson 1 and Bishop 1–3 now have doors on both sides. Bishop's common room,
three bedrooms, and the shared sitting room use indoor terrain and descriptions.
The ground entrance has solid footing and signage. All twenty bedrooms have a
single doorway to their house, with walls sealing accidental passages into
neighboring buildings or open air.

The old Rook 2/3 vnums (8998/8999) do not exist in the shipped areas. Two roof
spaces (9005/9001) are now enclosed upstairs bedrooms, connected to Rook's
landing. The resident and roommate slot order in `data/dorms.txt` is unchanged.
Existing assignments therefore use the repaired rooms without a data migration.

Rental ownership takes precedence over the overlapping fraternity coordinate
rules. Dorm keys also work through the academy lock checks, including opening
the bedroom door back into the common hallway. Other academy rooms retain their
existing restrictions.

Build and restart the server to load the code and area changes. Verification
boots a disposable copy of the world and exercises all twenty rentals, door
resets, movement, outsider rejection, roommate access, live rosters, inactivity
cleanup, and saved assignments:

```sh
make -C src -j4
python3 tools/run_dorm_integration.py
python3 tools/test_dorm_inactivity.py
```
