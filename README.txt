To compile the game go into src and use 'make' or to do a clean compile 'make clean' then 'make'
To run the game in a regular mod, go into bin and run startup like './startup&'
To run the game in a debugger go into area and do 'gdb ../src/haven' then 'run (port number)'
There is an Admin account included called 'Admin' with password 'admin'
To run the python script for AI stuff you'll need to do 'nohup python3 run_python_engine.py'

For executable-only GitHub updates from inside the game, see docs/game-updates.md.
Admins can use 'gameupdate build', 'gameupdate status', 'gameupdate install',
then 'copyover now'. Player/world data is never deployed by the updater.

For missing Linux/C++ headers in Windows VS Code, see docs/editor-setup.md.

Builds use the ignored src/.build-local/ cache; legacy checked-in object files
are not reused. Restart the server/debugger after rebuilding src/haven.
For the localhost command crash fix and regression test, see docs/command-dispatch.md.

For runtime indexes, AI queue cursors, save tracking, and optimization tests,
see docs/runtime-optimization.md.

For reliable AI queues, socket backpressure, social matching and note I/O,
including how to update the Python worker alongside the game, see
docs/runtime-hardening.md.
