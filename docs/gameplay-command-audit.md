# Gameplay command audit

This pass fixes reproducible command bugs and removes repeated work in combat,
operations and general gameplay. Existing local changes are preserved. It does
not constitute an exhaustive audit of every command or a gameplay rebalance.

## Fixes

| Area | Previous behavior | Result |
| --- | --- | --- |
| Combat movement | Approaching a target used its X coordinate for both axes. A single numeric coordinate also passed validation. | Approach uses the target's X and Y; coordinate moves require both values. |
| Combat action costs | Rejected moves consumed fatigue and cleared protection. A jump falling back to charge paid twice. | Rejected moves preserve those fields; the fallback pays once. Successful movement retains its existing cost timing. |
| Combat exits | Exit scans omitted southeast and nearest-exit checks inspected the character's room instead of the supplied room. | All ten directions and the requested room are checked. |
| Combat shortcuts | Charge, protect, jump, retreat and knockout formatted unrestricted input into 200-byte buffers. | Shortcut arguments use dynamically sized strings. |
| Combat coordinates and retreat | Large numeric inputs overflowed parsing, distance and vector arithmetic or rounded movement to zero. Retreat applied speed effects twice. | Movement parses bounded signed integers, uses wider geometry and applies retreat effects once. Direct vector scaling can recover a coordinate unit previously lost to rounding. |
| Operation selection | Bribe numbers counted hidden/completed records, unlike the displayed list. Orphaned faction records could crash listing. | List and actions share visibility rules and safely skip invalid records. |
| Operation withdrawals | An enrolled faction's withdrawal was capped against the host's troops. Requesting eight of its own two troops could create six manpower. | Withdrawals are capped against that faction's deployment. |
| Operation reinforcement | Failed or unauthorized requests could claim an enrollment slot. Capacity arithmetic could overflow. | Authority, funds and capacity are checked before enrolling; capacity arithmetic uses wider intermediates. |
| Operation completion | Bribing a pending operation retired the global battlefield operation instead of the supplied operation, leaving it available for another payment and troop refund. | Resolution retires the operation actually completed; repeat bribes cannot charge or refund it again. |
| Psychic operation completion | Psychic victories returned after battlefield cleanup without retiring the operation. | Both psychic victory paths retire the operation and clear its active state. |
| Operation planning after departure | Cancel, withdraw, reinforce, timeshift and launch commands could alter an operation while its troops already existed on the battlefield. | Those planning commands reject the active operation; list and info remain available. |
| Operation reminder wording | Reminders appended a legacy world name to the departure time. | Reminders keep the departure time and signup instructions without that name. |
| Drive state | Lists and rejected drives cleared hiding or driving-around state. | State changes happen after destination, travel eligibility and transit-room availability checks pass. |
| Garage recovery and location | Recovery destroyed the owner's key before refusing; recovery and location fees could overdraw the bank, and locating a garaged vehicle charged unnecessarily. | Rejected requests preserve keys and vehicle state; fees require sufficient funds and a valid service. |
| Returned vehicle leases | A returned lease retained its status and still granted town/world vehicle access despite its cleared cost. | Ownership checks exclude empty lease slots. |
| Offline abductions and searches | Temporary player loads leaked descriptors/characters; rejected targets ran quit/save logic; restricted attempts could activate bodyguards before refusal. | Eligibility rejections release temporary loads without quitting or saving; security checks precede live registration and guard activation. |
| Sleeping residents fleeing | Offline escape inserted a temporary player into a live room list, then freed the player. | Escape updates the saved destination without creating a dangling room occupant. |
| Cash | Decimal drops were rejected, floating-point conversion could lose cents, and large amounts could overflow conversions. | Drop/give parse exact cents, accept at most two decimal places and check transaction limits before changing balances. |
| Phone handoff | Giving a phone during a call to an NPC dereferenced missing player data. | NPC handoffs safely end the call; player handoffs retain transfer behavior. |
| Exit names and climbing | An unknown exit keyword selected the first exit. Climbing cleared a hide bit in communication flags. | Invalid names fail; climbing clears the actual hide flag and preserves unrelated communication settings. |
| Command dispatch | Non-ASCII leading bytes could index before the command table; numeric NPC input accessed player-only data; long internal input could overflow local buffers. | Hashing uses unsigned bytes, numeric player shortcuts exclude NPCs, and oversized input is rejected before copying. |
| Alias permissions | A hard-coded alias argument granted maximum trust. | The privilege-granting shortcut is removed; ordinary aliases still work. |

## Performance changes

- Combat movement reuses its base speed within one calculation instead of
  repeating equipment, skill and condition lookups.
- Reinforcement commands reuse their faction lookup.
- Unknown-command suggestions reuse the calculated trust level, skip candidates
  whose lengths make a match impossible, and compute each remaining edit
  distance once. Missing handlers are excluded from suggestions.
- The shared edit-distance routine stores one row of the matrix. Working memory
  is proportional to the shorter string instead of the product of both lengths.
  Exact results and the existing empty-input convention are preserved.

These reductions are established from the code and instrumented tests. No live
server latency or throughput improvement has been measured.

## Verification

Run from the repository root in Linux/WSL:

```sh
make -C src -j4
python3 tools/test_command_safety.py
python3 tools/test_command_dispatch.py
python3 tools/test_combat_commands.py
python3 tools/test_combat_coordinates.py
python3 tools/test_psychic.py
python3 tools/test_vehicle_commands.py
python3 tools/test_abduct_command.py
python3 tools/test_operation_command.py
python3 tools/test_operation_lifecycle.py
python3 tools/test_operation_schedule.py
python3 tools/test_operation_render_launch.py
python3 tools/test_operation_optimization.py
python3 tools/test_gameplay_commands.py
python3 tools/test_walking.py
python3 tools/test_phones.py
python3 tools/test_dissent_public.py
```

Focused tests exercise extracted production functions under ASan/UBSan. The
operation lifecycle test links the real release engine to check bribe completion,
repeated commands and battlefield victories in a disposable world. The
dispatch test links the actual release engine, boots a disposable world and
checks all 930 configured command handlers. Tests do not change live saves.

## Follow-up work

- Review general cross-room relative-coordinate and map-direction arithmetic;
  movement command parsing and its shared vector path are now hardened.
- Bound garage lease-price parsing and recurring-cost arithmetic, with explicit
  handling for extreme values already stored in legacy saves.
- Review inventory transfer ordering: `do_get()` can inspect or equip an object
  after `get_obj()` rejects a transfer or extracts a money object. This needs
  tests around ownership and extraction before changing the shared transaction
  flow.
- Consolidate repeated room lookups in `can_access()` and inventory scans in
  `has_dice()`, then measure the effect on representative workloads.
- Profile complete combat turns and operation launches with the existing
  `HAVEN_PROFILE=1` timing support before choosing broader optimizations.
- Operation rewards/report attribution, capture mechanics and previously saved
  privilege levels have not received a comprehensive audit in this pass.

Restart the running server/debugger after rebuilding to load the new executable.
