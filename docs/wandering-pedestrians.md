Wandering pedestrians are ordinary adult human NPCs who walk between existing
trolley stops. They have generic appearances, shirts, trousers, shoes, and
$2-$10 cash. Their skills and combat disciplines are zero, and they do not
attack. Only newly spawned characters marked `ACT_PEDESTRIAN` use this behavior;
existing NPCs, including shopkeepers, retain their existing rules.

Default settings in `src/pedestrians.c`:

| Setting | Default |
| --- | --- |
| Population limit, including captured pedestrians | 30 |
| Autonomous movement | One room every 15 seconds, staggered |
| Spawn/replacement rate | At most one every 2 seconds |
| LF available from each pedestrian | 1 displayed LF (100 internal units), once |
| Sick pedestrian replacement | After 30 real minutes, when unoccupied |
| Continuous binding timeout | 6 real hours |
| Knockout recovery | 10 real minutes |
| Hypnotized following | Up to 30 real minutes |
| Public hypnosis alarm chance | 20% per successful follow command |
| Unable to resume trolley walking | Replacement after 5 real minutes |

Use `attack pedestrian` or `knockout pedestrian` to attack a pedestrian. Combat
that exhausts their defenses knocks them unconscious. Public attacks trigger
the existing Cortex public-defense response, including its normal suppression
and duplicate-squad rules. Pedestrians can be bound, untied, carried, and dragged
using the existing commands. For example, `bind pedestrian hands` and
`bind pedestrian feet` restrain them. Restraints prevent autonomous walking and
following, but an eligible character can still carry or drag them through a
passable exit.

Use `bite pedestrian` or `victimize pedestrian` on a bound or unconscious
pedestrian. Biting requires a vampire or wight; ordinary command safety and
actor-state checks still apply. Both commands share the same single LF reserve.
The first successful drain grants 1 LF, adds **sickly** to the pedestrian's
intro, and empties the reserve. Later attempts report "They're drained dry."
The grant uses the `pedestrian drain` reason, which does not count as feeding
or reduce feeding penalties. Public draining can also summon Cortex defenders.

`hypnotize pedestrian follow` requires Hypnotism and makes an eligible,
conscious pedestrian follow through ordinary passable exits. The British
spelling `hypnotise` also works. `hypnotize pedestrian release` ends following
early. A successful follow command in a public room has a 20% chance to produce
the generic emote "Someone nearby shouts, 'HELP! MONSTER!'" and request a Cortex
ambush. The shout creates no witness NPC. Hypnosis uses the existing Cortex
alarm-enforcer response, while public attacks use the public-defense response.

Cortex enforcers retire when their target escapes or combat ends, is taken to
auction, becomes helpless, or suffers a critical wound. They stop attacking
immediately when retired and are removed by the next independent Cortex update.
Critical wounds retain the normal recorded Sanctuary eligibility and bleed-out
timer; removing the enforcers does not change recovery if the victim later dies.

Sick pedestrians leave after 30 minutes once they are no longer bound,
unconscious, following someone, or fighting. Those same conditions reset the
stuck timer: inability to walk must persist for five minutes after the
pedestrian becomes available again. This also replaces pedestrians left away
from the trolley street network. After six continuous hours with either hands
or feet bound, a pedestrian disappears with Sanctuary rescue flavor text; no
Sanctuary service, payment, or recovery record is created. Completely untying
them resets the binding timer. Captured pedestrians remain part of the
population limit until removed; replacements are fresh, healthy NPCs.

`src/pedestrian_routes.c` shares a bounded street graph and reverse shortest
distances among the population. Routes use existing public outdoor Earth
streets and real exits, respecting closed/locked doors, walls, and traversal
requirements. The cache refreshes every five minutes; a blockage can request
one shared rebuild after at least a minute. Each search covers at most 4,096
rooms and 32 stops. Individual movement checks at most ten exits and sends
room-local messages without world pathfinding or the player movement routine's
global visibility scans. Hypnotized followers may enter ordinary interiors
through passable exits. Shopkeepers never enter this movement path.

Set `HAVEN_PROFILE=1` in the server environment to log minute-by-minute
`PERF pedestrian_update` calls, total, mean, and maximum milliseconds. Compare
these with overall update timings under normal play and simultaneous Cortex
incidents. The 30-person, 15-second defaults average two autonomous room moves
per second; Cortex combat remains an additional incident-driven cost.

Validation from the repository root under Linux/WSL:

```sh
make -C src -j4
python3 tools/test_pedestrian_routes.py
python3 tools/test_pedestrian_commands.py
python3 tools/test_pedestrians.py
python3 tools/test_cortex_cleanup.py
```

The first two tests run production route and command branches under ASan/UBSan.
`tools/test_pedestrians.py` builds `tools/test_pedestrians.cpp` against the real
engine and runs it in a disposable copy of the world; it requires the release
build above. Related regression tests include `tools/test_victimize.py`,
`tools/test_npc_optimization.py`, and `tools/test_dissent_public.py`.
