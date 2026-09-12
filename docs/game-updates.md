# In-game GitHub updates

`gameupdate` is available only to admins (trust 105 or higher) on Linux. It fetches the
`main` branch of `https://github.com/ParoxysmRPG/Paroxysm.git` by default. It compiles
a fresh `src/` snapshot inside `.updates/`, then installs **only `src/haven`**.
It never pulls, resets, cleans, checks out, or merges the live working tree.
Player saves, accounts, houses, ground items, areas, other data, commands,
startup scripts, and local source edits are not copied from upstream or deleted.

## One-time setup

1. Deploy these source changes and `tools/game_update.py` to the server, compile
   with `cd src && make`, and restart/copyover normally. Do not pull over live
   data to do this initial deployment; transfer the changed code/helper files.
2. Push these changes to the branch the updater will fetch. Builds lacking the
   `do_gameupdate` symbol are rejected so updates cannot silently remove this command.
3. Run the game under its normal unprivileged Linux account, with Python 3.8+,
   Git, make, g++, binutils (`nm`), and the existing crypt/curl development libraries
   installed. The account needs write access to `.updates/` and `src/` and enough
   disk space for a fresh source tree, build, candidate, and previous executable.

The command registers itself in memory at startup; no edit to `data/commands.txt`
is needed. As with existing game paths, the server runs from `area/`.
Every subcommand, including status and logs, also checks `IS_ADMIN` inside the
handler and rejects NPCs. Admin privileges follow the game's character trust
system; being another character on the same account does not grant access.

## Updating

```
gameupdate build
gameupdate status
gameupdate log
gameupdate install
copyover now
```

Wait for **READY** before installing and **INSTALLED** before copyover. Build and
install requests run in the background. The status includes the fetched commit;
the log shows the last 4 KB of `.updates/update.log` (the full log is on disk).
Only one operation may run at a time. Build timeout is one hour; fetch timeout
is five minutes. A failed build invalidates the previous candidate and leaves
the installed executable alone. Install verifies the candidate checksum and
refuses if someone changed `src/haven` since the build began.

Installation first saves a durable copy of the old executable, then atomically
replaces `src/haven`. The running process continues until an explicit copyover,
restart, or a crash followed by the startup script's automatic restart. The
existing copyover command performs its normal saves before loading the binary.

To return to the executable saved by the most recent install:

```
gameupdate rollback
gameupdate status
copyover now
```

If the game cannot start, run `python3 tools/game_update.py rollback` from the
server root and restart it. Rollback restores one previous executable; it does
not restore or change saved data. Keep `.updates/` to retain that backup. The
updater log is append-only; rotate it periodically when the updater is idle.

## Repository settings

Optionally create `game-update.json` in the server root (ignored by Git):

```json
{
  "repository": "https://github.com/ParoxysmRPG/Paroxysm.git",
  "branch": "main",
  "jobs": 2
}
```

`jobs` accepts 1–8. For a private repository, configure Git credentials for the
game's OS account or use an SSH URL such as `git@github.com:ParoxysmRPG/Paroxysm.git`
with an already configured deploy key and known host. Fetching is noninteractive;
do not put access tokens in commands or repository URLs because build logs show
the URL. Repository settings are controlled on disk, not by player input.

## Limits

This prevents the updater from overwriting live data with repository copies.
It cannot guarantee that new game code has no bugs or save-format changes. Keep
normal, consistent server backups and review updates before installation. A
binary rollback cannot undo data that newer game code already changed.

Builds execute the selected repository's Makefile under the server account; this
is not a security sandbox. Only use trusted branches. Updates requiring new areas,
data migrations, helper changes, Python engine changes, or startup changes need
separate reviewed deployment. The live `src/` files and Git HEAD remain unchanged,
so a later manual `make` builds those local sources, not the installed commit.

Test without loading or changing real game data:

```
python3 tools/test_game_update.py
python3 tools/test_game_update_permissions.py
```
