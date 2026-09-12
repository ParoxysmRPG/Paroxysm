# Runtime optimization

The changes preserve the existing player/world save formats and combat timing.
No production workload benchmark has been collected; the regression suite checks
behavior and verifies specific reductions in work.

## Equipment

Weather processing builds an operation-local `EquipmentSnapshot` with one walk
over the first 200 carried objects. All subsequent equipment queries use its slot
array. The first object in each slot wins, and an empty primary hand falls back
to the secondary hand, just as `get_eq_char` does. Wetting, snow and drying still
visit slots in the original order, including the historical hand fallback.

Do not retain a snapshot across inventory changes or gameplay callbacks. The
general equipment lookup remains available for callers that mutate inventory.

Appearance scoring also passes one explicit equipment snapshot through fashion,
coverage and shapewear calculations. Visibility and coverage queries have
snapshot-aware variants; their clothing-layer rules, exposed-region overrides,
blindfold/water rules and hand fallback remain unchanged. Individual appearance
displays reuse their attraction score for both its number and color. The rare
bonus comparison reuses the subject's outfit score while preserving its existing
comparison order and integer truncation.

## Combat and factions

`runtime_indexes.cc` tracks live characters and indexes active combatants in the
same newest-first order as `char_list`. A cursor holds an order number instead
of a container iterator across gameplay callbacks. Removing a character is safe;
activating an older character during the update retains its original position;
newly spawned characters wait until the next pass.

After inserting a character at the front of `char_list`, call
`register_live_character`. Call `unregister_live_character` before removing or
freeing one, and change combat membership through `set_combat_state`. Offline
characters can have combat state without appearing in the live index. The
existing room, validity-range and `fight_problem` checks still apply.

Faction ID lookup uses a lazy index. Creation, loading, sorting and renumbering
invalidate it; vector-size changes also trigger rebuilding. Duplicate IDs retain
the original first-match behavior, and invalid factions are treated as before.
Code that changes faction IDs or vector order must call
`invalidate_faction_index`. Character-name and territory-number lookup semantics
are unchanged.

Territory bonus queries resolve the character's three faction memberships at
most once per query, lazily when the first matching reward is encountered. There
is no persistent ownership cache: control and eligibility edits are visible to
the next query, and lazy reward initialization retains its original order.

Phone ownership updates use a lazy number index with first-match duplicate
semantics. Appending or loading entries changes the vector size and rebuilds the
index on its next use; updates append directly to an already built index.
Renumbering entries, reordering the vector or replacing it without changing its
size must call `invalidate_phonebook_index`. Unchanged owner strings are retained,
including when the caller passes the existing string, while inactivity is still
reset. Case-only owner changes remain observable.

NPC target searches evaluate each candidate's aggression once and lazily reuse
the attacker's ranged/melee preference and range for that search only. Movement
and attacks still select independently, so movement, cover, and effect changes
are visible to the next decision. Disabled movement/attack attempts skip target
selection; round processing, movement cooldown assignment, and `cfighting`
clearing retain their positions relative to the eligibility checks. Skipped
attacks leave `attacking` unchanged; an eligible attempt with no target clears it.
Cover, ally and carrier lookups use the combat index with the original ordering
and eligibility filters. General targeting still considers noncombatants.

Combat membership checks reject distant bystanders before calling their nested
enemy search. Nearby checks retain visibility and turn-state handling. Search
limits remain in place, but distant bystanders no longer run nested scans that
could themselves increment `fight_problem` merely for exhausting the world list.

Operation report appends reuse the current allocator bucket when possible and
copy into a larger bucket only when necessary. Shared loaded strings are copied
before modification. The `char*` fields, report rollover rules, immediate read
visibility, and save formats are unchanged. `append_report_text` only accepts
strings owned by `str_dup`/`fread_string`; it must not receive stack buffers,
string literals as the destination, or independently sized allocations.

## AI result queues

The consumer reads one complete record and persists a small `<queue>.cursor`
file instead of copying the backlog after every record. It compacts after at
least 1 MiB has been consumed and the consumed prefix is at least half the file.
The old cursor is committed before atomic replacement of the queue. Its inode
identity lets a restarted consumer recognize the compacted suffix.

Producers must append while holding the existing stable `<queue>.lock` file and
reopen the queue path for each append. Partial final lines are left pending, and
a busy lock returns immediately. Existing queues without a cursor start at zero.
The external Python producer is not present in this checkout; these locking and
append requirements also applied to the previous rename-based consumer.

The cursor is local to an inode. Replacing the queue starts reading from zero;
truncating below the cursor also resets it. For migration or backup restoration,
export the unread suffix under the queue lock and restore it without a cursor.
Do not delete a live cursor or truncate and refill the same inode: doing so can
replay or skip records. As before, consumption is acknowledged before dispatch
to gameplay; this is not an exactly-once job execution system.

## Saves

Group texts now use explicit dirty tracking. Creation,
membership edits, delivered messages and loading mark them dirty. A clean save
returns before opening or serializing a snapshot. The earliest 90-day expiry
also schedules a save, retaining the strict original boundary. Clock rewind,
missing output files and failed saves are handled; only successful saves clear
the dirty flag. New group-text mutation paths must call `mark_grouptexts_dirty`.
Text histories and profiles use the same dirty/expiry rules. History delivery
and record insertion call `mark_texthistories_dirty`. Persisted profile writes use
`edit_profile`, and insertion/loading/reordering calls `mark_profiles_dirty`.
The shared string editor also marks profile fields on every editing call, so a
save during an open editor session cannot hide later edits. Profile lookups and
the transient `last_browsed` field do not dirty a save. Future mutation paths must
use these hooks; other datasets retain their staggered snapshot saves.
Opening an empty text field also avoids reading before the string buffer.

Ground-object saves serialize the original object traversal once and commit the
same bytes to the primary and rotating backup files. Both destinations retain
byte comparison, atomic replacement and independent error handling; failure of
one destination does not prevent attempting the other. A serialization failure
leaves both existing files intact. Death-transfer transactions are unchanged.

## Build organization

Timed-action completion lives in `process_actions.c`, extracted from `skills.c`
without changing the function bodies. It covers crafting, treatment, rituals and
research. Each build configuration now keeps its linked executable in
`.build-local`; repeated builds check file identity without reading the binary
or relinking. Switching configurations atomically installs a hard link to the
matching cached binary, preserving the inode used by any running process. The
build cache and installed executable must be on the same filesystem. Replace
executables through rename rather than modifying an installed binary in place.

## Verification

Run from Linux/WSL in the repository root:

```sh
make -C src -j4
python3 tools/test_runtime_optimization.py
python3 tools/test_phone_delivery.py
python3 tools/test_recovery.py
python3 tools/test_memory_safety.py
python3 tools/test_operation_optimization.py
python3 tools/test_operation_render_launch.py
python3 tools/test_npc_optimization.py
python3 tools/test_npc_engine.py
python3 tools/test_dissent_public.py
python3 tools/test_look_optimization.py
python3 tools/test_balance_rules.py
python3 tools/test_command_dispatch.py
python3 tools/test_feeding.py
python3 tools/test_guest_progression.py
python3 tools/test_focus_progression.py
python3 tools/test_psychic.py
make -C src BUILD=debug SANITIZE=1 -j4
python3 tools/test_runtime_optimization.py --sanitize
python3 tools/test_npc_engine.py --sanitize
make -C src -j4
```

Integration tests run against disposable copies of the world. The runtime test
checks queue restarts and compaction, equipment equivalence and weather effects,
combat ordering and ticking, faction invalidation, and save serialization counts
using the real engine. Existing `HAVEN_PROFILE=1` logs can measure actual pulse
and subsystem latency under representative player activity after deployment.
