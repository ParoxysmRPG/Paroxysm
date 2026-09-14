# Warfare patrol lifecycle

Warfare preparation keeps both teams in the defender's room. The existing
patrol visibility rules hide opposing teams until combat begins. Picking a
room several exits away based on sound propagation could put the attacker
outside combat range: the old code entered combat at distance 300, then
`check_fight` immediately removed both participants.

Both search expiry and `patrol attack` now use the same combat transition.
It brings the participants into range, resets stale room coordinates, and
checks that combat actually started. A refused start preserves preparation
for a later attempt. `patrol wait` pauses the shared countdown and
`patrol search` resumes it.

Invitations and assistants retain a pointer to their opposing leader.
Expired invitations and missing opponents clear patrol state without
teleporting into an abandoned event. Joined assistants enter combat and
receive warfare defeat handling immediately. A zero timer does not allow
the bare `patrol` command to clear an active warfare encounter. Other
characters cannot wake participants during preparation.

Run from the repository root under Linux or WSL:

```sh
make -C src -j4
python3 tools/test_warfare_patrol.py
python3 tools/test_warfare_wake.py
python3 tools/test_wakebound.py
python3 tools/test_syndicate.py
```

The warfare lifecycle test links the real engine and boots a disposable
copy of the world. It verifies combat survives subsequent combat and patrol
updates, rather than checking only the initial combat flags. The wake command
test runs the production command with AddressSanitizer and UndefinedBehaviorSanitizer.
The lifecycle test's optional `--diagnose-staging` argument reports the staging
distance and combat checks when comparing an older build.

Rebuilding updates `src/haven`; an already-running server needs a restart
or the normal copyover procedure to load it.
