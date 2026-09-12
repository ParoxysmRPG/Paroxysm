# Higher-power guests and earned remakes

An ordinary character on an account with at least 50 hours of play can create
an account-owned higher-power guest, without spending karma:

`guest higherpower <god/fae/demon/ghost/cthulian/primal> <name> [territory]`

Use `guest` to see guest types or `guest higherpower` to be prompted to choose
God, Fae, or Demon. `divine` remains an alias for `god`.

The territory is required before finishing creation and the claim is permanent.
If omitted from the guest command, use `change territory <territory>` on the creation screen. Finish the guest's
appearance in creation and use `done`. Existing higher powers without claims
must use `guest claim <territory>` before participating. The former shared
society avatar creation and switching commands now direct players to guests.

Society leaders declare relationships with:

- `society patron worship <higher power>`
- `society patron oppose <higher power>`
- `society patron none <higher power>` to clear one relationship
- `society patron none` to clear all relationships

Each society can have relationships with several powers. Both public and member
society info show worship and opposition. Cortex always opposes every current
and future higher power; no command or saved affiliation overrides this.

In the operation editor, choose the claimed territory and use
`goal worship <higher power>` or `goal attack <higher power>`. The sponsoring
organization must hold an actual core or society foothold there. Allied support
does not qualify. Worship requires public worship; attack requires opposition.
These operations must be open, scheduled at least two days ahead, speed 5 or
higher, and allow at least four PCs. They may run in peaceful territories.
They cannot be won through the operation bribe command.

Worship and attack show a required higher-power target in the editor. You may
also select `goal worship` or `goal attack`, then use `target <higher power>`;
the operation cannot be submitted without a valid target. This higher-power
field is only shown for worship and attack goals.

The targeted power can use `operation signup <number>` without society membership
or deployment settings. It joins the sponsoring side for worship and defends
itself against attacks. Other higher powers cannot join, and higher powers cannot
sign up for other operation goals. Signing up again withdraws participation.

The territory, foothold, target's availability and relationship are checked when
setting the goal, submitting the operation, launching it and resolving it. A
stale launch is cancelled and committed manpower is returned. Only the sponsoring
organization's actual victory applies the goal, once per operation. A different
winner or a failed operation earns no worship and does not banish the target.

Three successful worships unlock a T4 remake; five unlock T5. The player chooses
when to redeem with `guest remake t4 <new name>` or
`guest remake t5 <new name>`. Use `guest status` to inspect progress. Remaking
retires the guest and consumes all its progress. A successful attack resets all
worship and removes the power from play for 30 real days, including disconnecting
an online power. It cannot act, log in, receive worship or redeem a remake while
banished. After 30 days it returns with zero worship.

Monster guests earn T4 after exceeding their survival milestone and T5 after
exceeding twice that milestone. The milestone is captured at creation from the
existing monster-hours setting. Old monsters use that setting until remade.
Existing survival penalties still apply. Dead or already redeemed guests earn
no reward. A monster may remake directly or bank the reward by deleting and
then use `guest remake` from an ordinary character. As with the former nightmare
unlock, an account stores its best unused monster reward, not a stack of rewards.
Unspent legacy nightmare unlocks migrate to T4; existing nightmare characters
remain playable. New nightmare creation is disabled.

Remakes are permanent characters with an earned tier ceiling and no creation
karma cost. T4/T5 creation requires an earned guest reward. Existing permanent
characters remain playable; advancement by buying a higher T4/T5 tier also
requires the corresponding earned ceiling. Ordinary T1–T3 creation is unchanged.

Sanctuary switches off for everyone when **more than 20%** of eligible accounts
active in the previous **30 real days** have an active T4/T5 character. Each
account counts once, using its highest eligible tier. Guests, higher powers,
storyrunners, immortals, dead characters, characters in stasis and unfinished
creation characters do not count. Logging out does not remove a character from
the rolling population. Offline saves are read at startup/first population update
and hourly; live characters refresh each character update, and saves refresh
individual entries immediately. A separate activity
timestamp prevents offline maintenance saves from making players appear active.

Full and limited Sanctuary, their displayed status, and new ritual recovery
coverage all switch off together. The game announces both the suspension and
restoration and immediately saves a public news post for each change. The
posts explain that the concentration of powerful beings has overwhelmed
Sanctuary, or that the strain has eased and Sanctuary has stabilized. The last
state is saved with the news, preventing duplicate posts after a restart. At or below 20%, ordinary Sanctuary rules resume. Previously recorded
recovery incidents retain the coverage captured at injury, as required by the
existing recovery rules.

Claims, worships, banishment, retirement, operation completion, society
relationships, earned tiers and banked rewards persist across saves/restarts.
No production player or account data needs to be rewritten manually.

Verification (Linux/WSL):

```sh
make -C src -j4
python3 tools/test_guest_progression.py
python3 tools/test_recovery.py
python3 tools/test_operation_render_launch.py
python3 tools/test_balance_rules.py
```

The integration test links the real engine and uses a disposable world copy,
including a second process to verify persistence across restart.

The broader `test_core_factions.py` currently fails because its expected Scum
corruption position differs from both the checked-in and working seed data.
This is independent of guest progression.
