# Operation lifecycle fixes

## Causes and resulting behavior

- **Signup and launch disagreed.** The signup index accepted any positive
  deployment setting, while member selection required exactly `1`. It also
  counted players who could not deploy. The index now uses eligible connected
  players, accepts positive deployment settings consistently, and respects the
  selected society. Allied signups can supply the host/base owner's team even
  when that representative has no personal signups. Psychic operations do not
  require a society deployment switch.
- **Launch mutated shared identities and society ordering.** Failed attempts
  changed `faction`, and an alliance search selected the last matching team
  after shuffling the global society vector. Attempts now leave identity alone
  until accepted, prefer an exact team match, and shuffle only local candidates.
  Deployment power and participant counts are updated as slots are accepted.
- **A temporary combat team doubled as reward attribution.** Reward loops
  restored `factiontrue` while still counting players, so results depended on
  iteration order and whether someone had already left combat. Each deployed
  signup now records its earning society separately from its combat team.
  Member-power awards affect that society only; objective victories belong to
  the combat team. Per-operation defeat counters are reset, and unrelated
  operations cannot reuse an old battle's report or second-place history.
- **The general resource-sharing code duplicated the core share.** A primary
  society contribution now sends the existing 40% secondary shares once each
  to the core and second society. This sharing is intentional and distinct from
  which society earns the operation award or win.
- **NPCs reached player-only defeat code.** `wound_check` calls `prep_process`
  after operation defeat, including for NPC attackers. That function accessed
  `pcdata` before resolving a supported NPC to its player owner. The ownership
  check now comes first. Event logging still supports NPC actors and searches
  their room for a player patroller; personal log functions reject NPCs and
  missing player data. Null inputs are handled at these boundaries.
- **Operation defeat fell through ordinary injury handling.** Operation 0 DF
  now finishes through its nightmare-exit path, before real death, miscarriage,
  or immediate NPC extraction. Combat-index membership and incoming/outgoing
  target pointers are cleared before moving a defeated character. NPC deletion
  remains deferred through its lifetime timer. Battle completion and orphaned
  battlefield return use the same player wake/cleanup path.
- **Fast recovery was incomplete.** Severe operation injuries failed the
  treatment gate; later, their mild stage received a full ordinary timer.
  Operation injury provenance now survives saves and applies to both healing
  stages. Deployment rejects severe or worse wounds, including dead characters.
  A preexisting mild wound and its timer are captured before entry, preserved
  during the operation, and resumed unchanged after the new injury heals.
  Leaving without a new injury preserves that wound exactly. A new ordinary
  injury clears the operation recovery exemption.
  Older wounds without operation provenance retain their existing recovery
  rules; their origin cannot safely be inferred from the timer alone.
- **List ordering was only refreshed on load.** Every operation command now
  uses a stable sort by the actual scheduled departure, including appended and
  rescheduled operations. The schedule's day value counts occurrences of its
  departure hour, so sorting handles the midnight boundary correctly. List,
  info, signup, and other numbered commands use the same order.
- **Cover markers** again show the first two name characters in cyan instead
  of `[]`, retaining target colors, protection underlines, and turret markers.

## Verification

Run from the repository root under Linux/WSL:

```sh
make -C src -j4
python3 tools/test_operation_lifecycle.py
python3 tools/test_recovery.py
python3 tools/test_operation_render_launch.py
python3 tools/test_operation_command.py
python3 tools/test_operation_schedule.py
python3 tools/test_operation_time.py
python3 tools/run_combat_map_tests.py --sanitize
```

The lifecycle and recovery suites link the actual server and use disposable
world copies. They exercise launch, both NPC/PC 0 DF directions, combat cleanup,
the real healing update, recovery serialization, society awards, resource
shares, and repeated resolution. The isolated assignment, command, scheduling,
and combat-map suites use ASan/UBSan. No live world or player files are changed.
