Progression and Cortex rules

Tier 3 characters can learn one legendary power, tier 4 two, and tier 5 three.
Existing special handling for higher powers, guest monsters, and sin spirits
remains in place.

Tier 4 and 5 purchased discipline caps increase by 20%:

- Melee weapons: 96 / 144.
- Ranged weapons: 96 / 120.
- Combined supernatural defenses: 60 / 120.
- Combined mundane defenses: the existing focus-based cap multiplied by 1.2.
- Striking and grappling: the existing focus-based cap multiplied by 1.2.

Lower tiers and Science Augmented human defense caps are unchanged.

Civil Servant replaces Special Deputy, preserving archetype ID 9 and accepting
the old saved race name. Selecting the archetype or loading an existing deputy
assigns Cortex membership. Joining another faction/society, leaving Cortex,
and roster dismissal cannot remove that mandatory membership.

When Cortex participates in a live off-world operation and loses to an NPC
antagonist faction, there is a 25% chance of a breach. For the following real
hour, moving through Gravesend has a 5% chance per eligible move to spawn one
monster from that world, including on roads and inside buildings. A breach
produces at most one encounter. Monsters prefer a suitable level for the
player, falling back to the weakest available monster from that world.
The monster stays at the ambush location. Normal monsters retain their usual
location restrictions. The pending breach expires on server restart.

Cortex members travelling in dangerous rooms of the Other, Wilds, Godrealm or
Hell have a separate 5% ambush chance per eligible move. This requires an active,
unshrouded character outside combat, battlegrounds and hunting patrols, with no
existing spawned-monster cooldown. The encounter contains 1-min(4, tier+1)
creatures drawn independently from that world. A random difficulty (1-10)
sets the monster selection ceiling; the weakest local template is the fallback.
Actual combat disciplines also scale with tier, difficulty and an independent
75-125% roll per NPC. The normal 12-tick monster cooldown prevents repeated
spawns, and attackers expire after 12 ticks. Gravesend breaches are unchanged.

`society sellblood <glass>` consumes a nonempty giveblood glass to attempt an
NPC sale in waking Gravesend. One attempt per character per seven real days is
persisted as LastBloodSale, shared across society selections. A 50% sting roll
spawns a tier-scaled Cortex arrest squad and earns nothing. Otherwise the
selected active society receives $2,500 at tier 5, doubled for each lower tier
up to a $20,000 cap: $5,000 at tier 4, $10,000 at tier 3, and $20,000 at tiers 2 and 1.
The payout goes directly to society funds, with a society log and contribution tracking. Both
outcomes consume the glass and cooldown; invalid attempts consume neither.
Sales require being free to act, exclude guests, staff, ghosts, higher powers,
battlegrounds, dissent and state-of-emergency scenes, and refuse existing
enforcer pursuits. Rewards and cooldowns are saved immediately.

Validation: `python3 tools/test_blood_sales.py` exercises sale outcomes, cooldown
boundaries, eligibility, NPC counts and discipline scaling under ASan/UBSan.
`python3 tools/test_dissent_public.py` covers public-defense and arrest outcomes.
After building, `python3 tools/test_world_changes.py --enforcers-only` checks
real player save/load, the blood template, live enforcers and auction handling
in a disposable world copy.

Full or limited sanctuary prevents both direct hypnosis locking and a failed
resistance attempt from making a compulsion permanent. Ordinary temporary
imprints remain available, and existing locked imprints can still be unlocked.

Each territory grants one reward. District 82, Lauriea, and Rhagost grant
their existing monthly potions and no additional bonus. The remaining 80
records share 17 bonuses, with each appearing four or five times. Duplicate
bonuses do not stack. Navorost now grants Import-Export; the separate legacy
daily treasure payout is removed to avoid awarding it a second reward.

Brown Student is no longer available for character creation or archetype changes.
Only Cortex members can acquire College Contracts.
Students on campus receive a stored influence imprint, "serve Cortex", displayed
as "You mildly want to serve Cortex." It cannot be satiated on campus and is
removed immediately when they leave. It uses the normal imprint slots and save
format; if all 25 slots are occupied, it waits until a slot becomes available.
New accounts begin with zero karma, personal karma, and banked karma.
