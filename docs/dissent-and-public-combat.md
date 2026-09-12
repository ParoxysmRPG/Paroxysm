Dissent is a waking-world patrol between Cortex and player societies. An
eligible player on patrol has a 5% chance per patrol launch check to trigger
one when both Cortex and a society have available players in Haven. A saved
start time enforces at least seven real days between dissents, across restarts.
The patrol will not launch if that cooldown cannot be saved.

One NPC named "a crowd" appears on a ground-level town street. Its description
and announcements identify it as a dissenting mob protesting Cortex. It stays
in place, can be targeted with `attack crowd`, and does not attack bystanders.
Announcements and `patrol dissent` report its actual room, area, map coordinates,
and remaining time. Player societies must keep it alive for 30 real minutes;
combat does not extend the deadline. Reducing its defenses to zero knocks it
out and suppresses the protest.

Success awards every valid player society 1,000 resources ($10,000), including
societies whose members are offline. Failure awards Cortex 10,000 resources
($100,000). Core and NPC factions receive no society reward. The result pays
once and is recorded in the recipients' logs. Administrative removal or a
server restart cancels an active protest without paying either side; the
seven-day cooldown remains.

Public streets can have fights with Cortex intervention where existing target
rules permit combat. Explicit `ROOM_PUBLIC` target exclusions remain in place;
the dissenting crowd is their only new exception. Existing breach/enforcer
exceptions remain intact. Public vehicle attack restrictions are unchanged.

Starting an eligible public fight brings two to four Cortex enforcers to defend
the person attacked. They target only the original attacker, subdue them without
increasing their wounds, then withdraw. The attacker remains unconscious in the
same location at the defender's mercy. This response does not heal the attacker
or trigger the older public-alarm monster encounter.

An active dissenting mob in either combatant's room suppresses enforcer arrivals.
Public-response squads withdraw if their attacker enters a dissent room or the
nightmare, disappears, or is already subdued. Neither dissent participation nor
the new public response applies in the nightmare or deep nightmare.

Validation: `python3 tools/test_dissent_public.py` exercises production functions
with address/undefined-behavior sanitizers. Build with `make -C src -j4`.

Player societies no longer need a minimum operating balance or reserve above
the actual spending amount. This covers supplies, crafting, medical payments,
blessings, rescues, banishments, territory actions, and service activation and
upkeep. Service prices still scale with membership, and upkeep accounts for
the combined cost of active services. Bonus settings and other society actions
with no immediate charge no longer require an 80k balance. Existing authority
and stasis checks remain; core and NPC faction purchase minimums are unchanged. Recurring service upkeep
now follows the same per-member costs and affordability rules for all factions
and societies; unfunded services are disabled even for core factions.

`python3 tools/test_society_spending.py` checks exact-cost purchases, insufficient
funds, authority, service setup and cumulative upkeep under sanitizers.
