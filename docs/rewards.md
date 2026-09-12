Community credit is retired. Every account has access to the former reward
features: OOC and Legends channels, otell, trollreport, custom manifestation,
walk, rank and discipline, ghost return, all 20 shadow attack slots, account
renames and magic bandaids. Renames and bandaids no longer require consumable
balances. Existing gameplay requirements (tier, treatment, location, playtime,
guest restrictions, bans, and death timers) still apply.

Each account receives three item recolors per real UTC calendar month. Unused
recolors accumulate, including offline months. Existing balances are preserved.
Existing accounts accrue from September 2026; newly created accounts accrue
from their creation month. `credits` shows the balance; use `color` instead of
`done` when customizing an item to spend one recolor on a successful edit.

`credit namecolor (0-255)` colors your name on the who list.
`credit saycolor (0-255)` colors your speech between double quotes in emotes
for everyone who sees it. Both accept `default` to reset, save per character,
and cost no item recolors. `credit` displays both settings and the available
item recolor balance. The standalone `saycolor` command retains its existing
reader-side speech preference.

The account save field `ColourMonth` records the last credited month. Old account
files without it migrate automatically. Recolor spending saves the character
and account. Old donation fields remain readable for save compatibility but
no longer control access; `donatechar` no longer issues credit or payouts.

Validation: `python3 tools/test_rewards.py` (Linux/WSL), and `make -C src -j4`.
