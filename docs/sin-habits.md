# Sin habits

`habit sin murderer`, `habit sin scammer`, and `habit sin corrupt` choose the
form of harm behind a character's power. Anyone can select a habit; recurring
consequences and tier prompts apply from effective tier 3 upward. `habit` and
the existing trusted storyteller habit report show the selection.

- **Murderer:** retains the established portrayal and tier prompts, with no new
  periodic event. This is the save-compatible default for existing characters.
- **Scammer:** financially ruined victims send one furious or desperate text
  from **Unknown number** every 14–18 real days, when a working phone with
  signal and inbox space is available. Ten personal vignettes cover lost homes,
  retirement, livelihoods, family trust, and small necessities. Messages use
  the normal inbox and silent/beep notifications. They create no player contact,
  conversation history, rewards, or copied-text scheme events.
- **Corrupt:** every 28–42 real days, an ordinary person may confront the
  character about someone harmed by their corruption. Five accounts cover
  suppressed complaints, unsafe housing, buried evidence, retaliation, and
  poisoned water. One unarmed vigilante has 25 HP and only 5 Striking and
  5 Toughness, with 1–3 base damage per hit, irrespective of the player's tier.
  The name, room appearance, description, and encounter introduction explicitly
  identify this person as virtuous and seeking justice for innocent victims.
  Two Cortex enforcers assist the player against the vigilante on the public
  street. Their intervention makes clear whose interests Cortex protects.
  This is an easy encounter about the harm done. Defeating the vigilante ends their attack; losing leaves
  the player knocked out at the exact room and coordinates where they fell,
  without added wounds, death, capture, relocation, or lost possessions.

Newly tracked characters receive a full interval before their first event.
The deadline, habit, and last vignette persist. Logging out counts toward the
deadline, but there is no backlog: a successful event starts a fresh interval.
Changing habits or tier does not clear an existing deadline. Consecutive events
do not repeat the same vignette. Failed delivery stays pending without output.

Events wait while the player is AFK, linkdead, asleep, helpless, dreaming,
shrouded, or fighting. Staff, guests, ghosts, and dead characters are exempt.
Vigilantes wait for an uninjured player at full HP on a public outdoor Earth street,
outside private/safe rooms, prison, travel, institute grounds, and nearby fights.
They target only that character, cannot switch to bystanders, and withdraw if
their target leaves or becomes unavailable. Public-room combat protection
allows the encounter's two participants to fight each other. Both vigilantes
and assisting enforcers require a public street, using the game's `public_room`
rules, and withdraw if it ceases to be public. Enforcers target only the
vigilante confronting the player they protect, never the player or bystanders.
They withdraw when that vigilante is defeated or leaves; no reinforcements
are added during the encounter.

Sin does not change independent vampire feeding or werewolf lunacy habits,
feeding hunger, or society rules. Scammer and Corrupt tier prompts ask about
financial harm and abuses of power instead of assuming a murderous history.
`help sinhabit` explains the feature; the separate `sin set` cardinal-sin
command and its existing help remain unchanged.

Verification (WSL/Linux):

```sh
make -C src -j4
python3 tools/test_sin_habits.py
python3 tools/test_phones.py
```
