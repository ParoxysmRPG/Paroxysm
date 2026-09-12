# Recovery and correctness pass

Recovery uses the existing `get_hour(NULL)` server clock and respawns at
a randomly selected trolley stop, with equal chances for each distinct existing
stop in `trolly_stops`. An incident exactly at 06:00 is scheduled for the following
06:00. Login and the daily offline scan also process overdue records.

| Incident coverage | Death | Maim | Organization charge |
| --- | --- | --- | --- |
| None | Remains dead | Remains maimed | None |
| Ordinary Sanctuary | Next 06:00 | Next 06:00 | Captured payer |
| Ritual (`AFF_UNDERSTANDING`) | Next 06:00 | Next 06:00 | None |
| Forest monster / ambush | Remains dead | Remains maimed | None |

The existing `forest_monster()` test identifies NPC prototypes 10–50. Monster
abduction and lair incidents also pass their encounter source explicitly.
Ordinary NPCs are not exempt from Sanctuary recovery.

Each maim retains its own coverage. The engine has a single critical severity
and bleed-out timer; the incident that first makes the wound critical owns its
provenance. Reapplying that severity does not overwrite it. Bleed-out death
inherits this record, including its payer and forest override, and schedules
recovery relative to the death. Later gains or losses of Sanctuary do not change
existing injuries. Old saves without incident metadata remain uninsured.

`SANCTUARY_DEATH_COST` and `SANCTUARY_MAIM_COST` in `src/recovery.h` are 5,000
and 1,250 resource units ($50,000 and $12,500) at T1. Both charges multiply by
the recovered character's current tier, capped at T5:

| Tier | Revive (resources) | Per-maim heal (resources) |
| --- | ---: | ---: |
| T1 | 5,000 | 1,250 |
| T2 | 10,000 | 2,500 |
| T3 | 15,000 | 3,750 |
| T4 | 20,000 | 5,000 |
| T5+ | 25,000 | 6,250 |

Payer priority is current society,
legacy society, vassal organization, core faction, then selected faction. If no
organization existed at the incident, recovery has no organization to bill.
A missing previously captured organization leaves its recovery pending.
Recovery debits can leave a treasury in debt; automatic floors and balance caps
do not erase it. Existing purchases, upkeep, theft and explicit administrative
transactions remain in place.

Hyper Regeneration retains its existing healing rules and corpse timer. Its
own recovery never enters the billing path. It does not automatically insure
otherwise uninsured incidents. Sanctuary no longer blocks ordinary hostile
actions, while sexual commands check protection both when requested and when
completed. Existing consent handling remains in place.

Normal carried, worn, held and nested items move as original objects into the
corpse, including on vampire and forest deaths. Virtual wardrobe storage remains
separate. Recovery does not clone or return corpse contents. Player/ground saves
use a durable prepared transaction so a restart can finish an interrupted
ownership transfer. Boot replays it before loading either save. A failed death
commit stops the engine rather than allowing later saves to overwrite a partial
transaction. Recovery receipts are saved atomically with organization balances;
replaying a stale player save does not charge again, even after a reboot.

Dead operation participants use the existing spectre equipment and return path.
Their normal-world dead state is restored on return. Recovery defers while they
are participating. Operation scheduling, objectives, matching, scoring and
rewards retain their existing logic.

Territory benefits use all three actual foothold holders. Saved capture history
tracks these holders independently; migration and alliance changes do not create
a capture payment. Allied organizations without a foothold receive no direct
benefit.

## Validation

`tools/test_recovery.py` links the production engine and runs in disposable copies
of the world, player and organization files. It covers coverage and forest
matrices, critical provenance changes, mixed maims, original inventory ownership,
offline overdue processing, payer changes, stale saves, fresh boot, transaction
replay, Hyper Regeneration, operation wake/return, treasury persistence and
focused-description edge cases. Run it normally and with `--sanitize` after
building the corresponding configuration.

The matrix uses the actual `pc_update` bleed-out path and exercises all 72 scene
field editors with combined output larger than the old fixed buffer. Socket
tests cover oversized ident replies and repeated ordinary disconnects. The
release and sanitizer configurations use separate temporary link outputs.

Other regressions: `test_memory_safety.py`, `test_command_dispatch.py`,
`test_alliance.py`, `test_territory_rewards.py`, `test_look_optimization.py`,
`test_operation_optimization.py` and `test_operation_render_launch.py`.

The existing `test_core_factions.py` profile assertion expects different Scum
ideology values from the checked-in `data/clans.txt`. This pass does not change
those profile values or make the Order joinable.

This is not a warning-free build. Legacy formatting/possible-truncation warnings,
array-address comparisons and unused-result/declaration warnings remain. No
warning suppression flags were added. Full compiler logs are retained under
`src/.build-local/` for follow-up review.

Final forced release rebuild succeeded. Its complete output contains no errors,
`-Wmaybe-uninitialized`, `-Warray-bounds`, `-Waggressive-loop-optimizations`,
`-Wrestrict`, embedded-NUL, division-by-zero, null-file or string-overflow
diagnostics. It still reports 139 `-Wformat-overflow` and 11
`-Wformat-truncation` diagnostics; these are not certified harmless.
Recovery/scene and memory-safety suites pass under ASan/UBSan; release recovery,
memory, command-dispatch, look, alliance, territory and operation regressions
also pass. The core-profile fixture mismatch described above remains.
