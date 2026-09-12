# Command dispatch and localhost crash regression

The September 2026 localhost crash occurred when `s` matched `society` before
the explicit south shortcut. The running binary lacked `do_society`, leaving
that command with a null function pointer that `interpret()` called directly.
The committed `.build/release-sanitize0/clans.o` still exported `do_cult` and
`do_sect` despite its newer timestamp, so an incremental build reused old code.

Exact command names and shortcuts now take precedence over abbreviations,
within the character's trust level. Other abbreviations retain table order
among commands with loaded handlers. An unavailable exact command reports an
error, and its name and missing handler are logged. The command remains in the
table for inspection and repair through the command editor. Explicitly disabled
commands and their handler aliases still obey the existing disable checks.

The missing `newalliance` handler now recalculates the single society alliance
pool. It takes no arguments and retains the configured maximum-level access.
The handler also checks that permission when called directly.

The Makefile uses the ignored `.build-local/` cache rather than committed
objects. Linking succeeds before the previous executable is replaced. A running
server or debugger must be restarted to load the replacement executable.

Startup creates `back1` through `back7` under the existing `data`, `accounts`
and `player` directories. This addresses the separate backup-write errors in
the crash log. Directory creation failures are logged with the path and OS error.

## Verification

In Linux or WSL, from the repository root:

```sh
make -C src -j4
python3 tools/test_command_dispatch.py
python3 tools/test_alliance.py
```

The command test links actual release objects, boots a disposable copy of the
world, and sends commands through alias substitution and the interpreter. It
checks every configured handler, exact movement shortcuts, missing and empty
handler names, trust restrictions, disabled commands, real society/alliance
handlers, movement, and backup creation/writing. Live saves are not changed.

The existing `test_core_factions.py` additionally expects the Scum's corruption
axis to be `AXES_MIDLEFT`; the current saved profile is neutral. That separate
profile/test mismatch is outside this crash fix. The `limbo.are` item-type
warnings in the original boot log are also separate from command dispatch.
