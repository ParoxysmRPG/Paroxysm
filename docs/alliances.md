# Societies, factions and alliances

Players can join one player society or one faction. New memberships and society
creation cannot combine the two. Existing extra memberships are preserved until
left; leaving does not open an extra slot while another membership remains.
`society select <name>` selects a preserved society for commands, comms,
deployment and operatives. `ssay` communicates with its alliance.

Each character can create only one society ever. Successful creation is saved
permanently on the character; leaving or disbanding the society does not reset
the limit. Failed creation attempts do not count. Older character saves have
no creation history, so the limit tracks creations from this change onward.

Player societies use one category, `FACTION_SOCIETY`. They start without a
higher-power affiliation. Leaders can choose `society patron worship <name>`,
`society patron oppose <name>`, or `society patron none`. The relationship is
stored separately from society type. Society and character secrecy have been removed from resource costs, gains,
operation rewards, alchemy and intel. Legacy save fields remain readable.

Society service setup and all faction/society upkeep scale linearly with all
named roster members, including inactive members, with a minimum of one.
Faction setup retains its existing base rates and activation requirements.
Recovery fees are separate and scale by the recovered character's tier.

| Service | Society setup per member | Faction/society upkeep per member |
| --- | ---: | ---: |
| Sanctuary | 100 | 200 |
| Corpse disposal | 100 | 100 |
| Scouts | 25 | 10 |
| Scanner | 25 | 20 |
| Comms/transmitter | 30 | 10 |

Amounts are resource units ($10 each). Upkeep uses the existing faction update
schedule. Societies need only the actual setup fee to activate a service.
Upkeep for all factions and societies requires only the combined actual cost,
with no reserve requirement or additional core-faction percentage surcharge.
Services are funded in sanctuary, scouts, scanner, comms, then corpse disposal
order; an unaffordable service is disabled, including for core factions.
The existing college sanctuary exemption remains. Enabled services can always
be switched off without a fee.

The core records in `data/clans.txt` directly define the new factions:

| Faction | Corruption | Democracy | Supernatural | Other positions |
| --- | --- | --- | --- | --- |
| Cortex | Strongly corrupt | Strongly authoritarian | Strongly against | Neutral |
| Scum | Moderately corrupt | Strongly democratic | Moderately for | Neutral |

Neither has the former combat/arcane admission requirement. Contacts use
Cortex/Scum names. The Order is closed to player joining, including creation
and operatives; its manifesto describes its destruction by the Cortex.
IDs 5, 6 and 7 stay stable to preserve references. There is no runtime
Hand/Temple renaming layer.

The supernatural position does not modify lifeforce, admission age, trust or
standing. Strong anti-supernatural positions permit natural members to track
or incapacitate supernatural members through faction chip control; strong
pro-supernatural positions reverse this. Lesser stances impose no such chip
control. Corruption's existing tier-based chip control remains independent.

## Two alliance sides

Eligible factions and player societies share exactly two sides: left and right. The current issue
determines their displayed names. `src/alliance.h` defines persisted IDs;
use `alliance_sides` and `is_alliance()` rather than a numeric range. The right
side retains ID 3. Core factions persist their strategic side in `AllianceSide`;
their legacy core affiliation remains available to existing operation matching.
Nonparticipants and the destroyed Order have no strategic side.

Positions below neutral join left and those above neutral join right. Neutral
societies keep a valid allegiance or use their stable faction ID to break a
tie. Old eligible core records with unset positions receive a stable side.
Balancing uses one faction-and-society pool,
excludes nonparticipants, and prefers the current issue when scores tie.
Changing an arrangement applies the existing standing/member-power penalties
only to organizations switching sides and halves shared territory support once.
It does not debit or normalize treasury balances. Repeating an arrangement has
no further effect. Direct territory bonuses follow individual foothold holders.

## Existing saves

- Old society types 3/4 load as one type. Existing higher-power relationships
  become optional opposition/worship respectively. Explicit `PatronRelation`
  values take precedence on subsequent loads.
- Old `FCult`/`FSect`, esteem, deployment and operative keys remain readable.
  New saves write `FSociety`/`FSocietyLegacy` and corresponding society keys.
  A sole secondary membership moves to the primary slot with its associated
  state. A second existing society stays accessible until left.
- Former middle support in slots 2/12 is distributed between surviving sides.
  The old secondary bank then merges into shared support, capped at 100% per
  side, and is zeroed. Migration is repeatable. Existing left/right affiliations
  survive; retired middle affiliations are assigned without costs.
- `Phil` retains its twenty-position layout for core influence and world data.
  Both historical society base slots remain usable; new bases use a free slot.
- Weather retains obsolete fields as reserved zeroes so later fields do not
  shift. Old values are consumed without driving a separate alliance pool.
- Rosters, resources, faction IDs and historical memberships are retained.
  Normal saves persist conversions. Older executables are not a supported
  rollback after saving the new format.

## Verification

Run in Linux or WSL:

```sh
python3 tools/test_core_factions.py
python3 tools/test_alliance.py
python3 tools/test_operation_optimization.py
python3 tools/test_operation_render_launch.py
make -C src -j4
```

Focused tests compile production helpers with engine stubs and address/undefined
behavior sanitizers. They cover membership rules, preserved memberships,
secrecy decay, profiles, LF/chip behavior, repeatable support migration,
relationships, displays and balancing without mutating game saves.

Higher-power relationships can now name multiple powers. Cortex permanently
opposes all powers. See [guest progression](guest-progression.md) for territory
claims, worship/attack operations, earned T4/T5 remakes and global Sanctuary.
