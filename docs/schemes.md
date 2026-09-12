# Scheme discovery

Unrevealed ongoing entries in `scheme list` show their shared number and
`A SCHEME IS UNDERWAY`. They reveal no author, type, introduction, description,
or thwart fee through `scheme info` or news until successfully investigated.
Authors know their own schemes. Completed schemes retain public history.

Use `scheme investigate <number>` to roll d100 + 10 times professional focus
against the schemer's d100 + 10 times saved launch focus + 5. Ties favor the
schemer. Both sides also add +5 per Socialite focus rank, on top of professional
focus. The defending bonus is recorded at launch, including for limited schemes.
Each direct attempt costs 500 regular/scheme influence, win or lose.
There is no minimum-focus gate: lower-focus investigators can win the roll.
Failure reveals nothing and can be retried. Already-known or invalid requests
are not charged. Research orders use the same roll with their existing fee and
delay, without charging another investigation fee at completion.

Successful discovery is per character and saved in the existing research list,
including backups. Previous research results remain valid. Matching uses exact
character names, so a name prefix cannot inherit another character's discovery.
Discovery unlocks the detailed listing, info, news introduction and thwarting.

List and news access perform no offline character loads. Only a contest against
a legacy scheme without recorded launch focus resolves the author online or
from their saved character, then caches and persists that focus. Failed author
loads do not grant discovery or charge direct investigation fees. Number lookup
is shared by scheme info, investigation and research orders; both contest types
share their dice formula. News publication stops scanning once a match is found.

Run regression checks under Linux/WSL with `python3 tools/test_schemes.py`.

# State of emergency

Use `scheme type StateOfEmergency` (or `scheme type state of emergency`).
It also works as a secondary type. Cost: 20,000 influence; base duration:
72 hours, with normal launch delays, duration modifiers and thwarting.
While active, public alarm checks (including visible weapons and blood),
public combat exclusions and Cortex public-fight responses are suspended.
Legacy police pursuit and new civilian assault police penalties are suspended.
Large weapons and armor do not prevent RPXP gain while the scheme is active.
Existing public-fight squads withdraw on their next update. Normal enforcement
resumes when the last active emergency ends; existing records are retained.

# Contested thwarts

`scheme thwart <number>` immediately attempts to end a visible, active scheme.
`scheme info <number>` shows the fee and availability. The challenger pays one
third of the influence originally paid at launch, rounded up, on either outcome.
Regular and scheme-only influence count. Normal launches record the higher cost
of the two effects; limited launches retain their existing half-primary-cost
pricing. Legacy saves reconstruct the price from those rules.

Each side rolls d100 + 10 times professional focus. The schemer uses their saved
launch focus, adds 5, and wins ties (55.35% with equal focus and Socialite bonuses). Successful investigation is required before a thwart attempt. The author can be offline; own-account thwarts and
storyrunner attempts are rejected before payment.

Failure sets a six-hour cooldown on the scheme for all challengers. The cooldown
and original cost are saved in primary and backup event files.
Each completed roll notifies the schemer of the challenger's name, scheme
number and success or failure, immediately online and in saved login messages. Success ends the
scheme, clears its ongoing global effects and introduction news, and increments
the successful challenger's thwart trackers. No scene karma or bystander rewards
are issued. Old accept/reject/refer/finish commands no longer resolve thwarts.

Schemes no longer require a thwart-method description or an available
storyrunner, and their lifetimes are no longer extended or shortened based on
scene availability. The ordinary activation delay and expiry still apply.

Socialite bonuses for older schemes are resolved with the author's saved
character on first contest, without overwriting recorded launch focus. Both
values are then cached and saved, so defense does not require the author online.
