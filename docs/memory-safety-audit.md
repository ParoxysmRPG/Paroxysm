# Compiler warning and memory safety audit

The fixes retain the existing save formats and distinguish storage indexes from
game IDs and coverage bit masks.

| Data | Intended capacity / meaning | Resolution |
| --- | --- | --- |
| `cover_table` | 18 body coverage masks, indexes 0–17 | Focused smell (18) stays in description order but never indexes this table or checks clothing. Default dream appearance explicitly excludes smell. Single-location and combined descriptions use the same boundary. |
| Object `value` | Six slots in prototypes and runtime saves | Both structures use `MAX_OBJ_VALUES`. Runtime clones and editor resets handle all six slots. |
| Fantasy rooms | 100 rooms with one safety flag each | Initialize safety flags with rooms, separately from the 200 participants and exits. |
| Group text numbers | Ten participants, including in persistence | Initialization follows the declared array extent. |
| Legacy clan division leaders | Five declared slots | Initialization and cleanup follow that extent. No active serialization or gameplay consumers of this legacy field were found; current factions use a separate structure. |
| Dorms | 20 residents followed by 20 roommates | Allocate 40 entries, initialize on load, and reject out-of-range persisted indexes. |
| Story conditions | Ten rows of three integers | Update only those ten rows. |

Object prototypes already had six values, and both runtime writers/loaders
already serialized six values. Area records intentionally vary by item type:
for example, containers use five values and initialize the sixth to zero.
Those record widths remain intact. Six-value clothing, jewelry, key, corpse and
ranged records now preserve all their fields instead of emitting constant zeros.
Potion output now matches its six-value numeric/flag reader, rather than emitting
five fields containing obsolete quoted spell names. Creation, cloning and
player/world save round trips exercise nonzero sixth values independently of the
following `rot_timer` field.

Self-referential `sprintf` appends now write at the existing terminator with
`snprintf` and the remaining array capacity. Output and spacing are unchanged when
they fit; oversized appends truncate at the destination boundary. Two redundant
self-`strncpy` calls were removed; truncation indexes are bounded. Small text
prefixes now include space for the terminator, and two weekly processing
`memset` calls use the actual destination size.

Sanitizer checks also exposed underlying issues:

- The allocator aligned permanent blocks to four bytes and put general-purpose
  payloads four bytes after an integrity marker. Both now retain
  `alignof(std::max_align_t)` alignment, including recycled blocks.
- Legacy `*_USED` bounds also serve as character-ID limits and can exceed the
  number of table rows. Table loops
  now use counts derived from the actual definitions. Character IDs and their
  storage capacities are unchanged.
- File string readers narrowed `getc()` results to signed `char`, confusing
  `0xff` with EOF and indexing the line reader's lookup table with negative
  values. They now retain integer input until classification is complete.
- Skin-score calculations squared elapsed minutes in `int`, overflowing after
  roughly a month without a shower. The square now uses `long long`, preserving
  the original float conversion and score formula.

## Verification

Run in Linux/WSL from the repository root:

```sh
make -C src -j4
python3 tools/test_memory_safety.py
python3 tools/test_look_optimization.py
python3 tools/test_command_dispatch.py

make -C src BUILD=debug SANITIZE=1 -j4
python3 tools/test_memory_safety.py --sanitize
make -C src -j4  # Restore the release executable.
```

The engine regression test copies world files into a temporary directory and
does not write live saves. It covers `look me`, focused smell/scent ordering and
visibility, clothing, xray, mermaids, one-character descriptions, both object save
writers, area record round trips, constructors, the final dorm roommate, invalid
dorm indexes, allocator alignment, bounded string appends and story conditions.
Sanitizer mode stops on the first address/undefined-behavior error. Leak detection
is disabled because the engine retains its permanent allocator pools until exit.

Additional checks: operation optimization and territory rewards tests pass.
Two broader tests fail outside the changed helpers: `test_core_factions.py`
expects Scum's corrupt axis to be `AXES_MIDLEFT`, and `test_alliance.py` omits
the `TerritoryRewardDefault` definition from its extracted test translation unit.
These faction-policy/test-fixture issues are outside this memory safety audit.
