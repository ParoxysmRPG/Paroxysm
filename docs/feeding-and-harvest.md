Feeding and harvest rules

Clinic arrest requests, bribes, approvals, and old arrest forms are disabled
with the reply `go capture them coward.` The implementations remain in place.
Existing clinic warrants no longer cause automatic capture. Physical capture
and commitment remain available.

Dream snares are disabled through the dream command, rituals, and prepared
battlefield actions. Pending snare rituals cannot complete. Saved dream-snare
flags and the associated weakness clear on load and during player updates.
Ordinary dream invasion remains available.

Tier 3 characters must feed every 30 real days, tier 4 every 21 days, and tier
5 or higher every 14 days. Logged-out time counts. Legacy characters receive
a full interval when first loaded with the new rules. Guests, staff, and dead
characters are exempt. Characters below tier 3 reset their hunger clock.

Reminders arrive once every seven real days while playing, including when
feeding is overdue. Each names the current hunger penalty (if any), the days
remaining until the next stage, and that stage's LF penalty or loss of sanctuary.
First symptoms begin only at the tier deadline; later stages begin every seven
days thereafter. Logged-out players receive one reminder when they return if
a week has elapsed, without a backlog of messages.
LF penalties persist through regeneration and increase as follows (displayed
LF units; 100 internal units equal 1 displayed LF):

| Time overdue | LF penalty | Sanctuary |
| --- | ---: | --- |
| Under 7 days | 5 | Normal |
| 7–13 days | 15 | Normal |
| 14–20 days | 30 | Normal |
| 21+ days | 50 | Full and limited protection disabled |

A positive LF gain from a vampire bite, psychic feeding, prisoner/victimize
feeding, or a sacrifice ritual restarts the clock and removes hunger penalties
immediately. Transfusions and unrelated LF grants do not count. Losing hunger's
sanctuary penalty restores eligibility under the ordinary sanctuary rules.
Both feeding timestamps and reminder timestamps are saved.
Every successful qualifying feed confirms that you are fully fed and gives
the 30/21/14-day interval until your next hunger symptoms, even if you were
not overdue. This confirms hunger satisfaction, not maximum current LF.

Victimize's positive response reward starts a full 30/21/14-day interval;
a short exchange is sufficient, with no separate monster_fed quota. The legacy
monster_fed counter remains save-compatible but no longer decays or causes
hunger warnings or automatic illness. Existing illness from other mechanics
is unaffected.

Victimize supports helpless, pinned, and dream-slave player targets in the
same scene. Targets have two minutes to select a response, with a reminder
at one minute. Selected responses finish on their next emote or automatically
after fifteen minutes. Pending responses cannot be overwritten or rewarded
twice. Leaving the scene or becoming free invalidates the interaction.
Response menus include tied rewards and only offer intel at 1,000 or more.
Bleeding has a consistent four-day cooldown.

Tier 4 characters cannot purchase Mental Discipline and receive
`You're too far gone to find salvation now.` Existing purchases are retained.

Cortex members collectively must harvest 20 raw LF per UTC calendar month.
Credit occurs only when a harvest finishes successfully and counts LF drained,
before alchemy or cylinder-value multipliers. The member's core membership
determines credit, regardless of their currently selected society. Surplus is
capped at the quota and does not carry forward.

At rollover the Cortex receives $2,500 in society resources if it met the quota,
or a $10,000 fine if it missed it. Each additional month missed during downtime
also incurs the fine. These fixed amounts bypass secrecy/resource multipliers,
and fines may put the society in debt. The result appears in the society log.
The first tracked month starts on deployment, without retroactive fines.

Only Cortex society/faction info shows the quota, and only to Cortex members
and immortals. Both named info and the member's default info include progress,
the UTC reset rule, the fine, and the reward. Quota progress and the settled
month persist in the faction save file to avoid duplicate rollover awards.

Use `affect` (or `help affect`) to see current lifeforce and its active
modifiers, including feeding hunger, stored gains/losses, society effects,
and wounds. Gains and losses are aggregate balances, not a victim history.
