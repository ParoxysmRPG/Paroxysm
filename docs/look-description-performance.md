# Look, description and exposure performance

Character appearance rendering now reuses an equipment snapshot within each
render. Clothing padding and output share the calculated visibility of each
occupied wear slot. Focused descriptions reuse each body location's coverage
result for its description, brand and scars, and check description order before
doing smell skill lookups. Location and default dream descriptions also reuse
equipment snapshots.

Expose and unexpose reuse equipment lookups throughout each command. Adjusting
one body location checks only that location, with at most two coverage checks.
Description announcement parsing reads the existing text without allocating a
copy that would otherwise leak.

Snapshots are local to the operation. They retain the existing first-item rule,
200-item lookup limit and hand fallback behavior. The next operation reads fresh
equipment and exposure state. Clothing concealment, water and blindfold rules,
x-ray restrictions, description order and output formatting are preserved.

For a fully described visible target, instrumented tests reduce focused
description snapshot builds from 54 to 1, coverage checks from 54 to 18, and smell
skill lookups from 21 to 2. Across 20,000 expose/unexpose comparisons, inventory
visits fall from 34,910,238 to 1,179,900 (96.6% fewer). These are operation counts
in test fixtures; live server latency and throughput have not been measured.

Run from the repository root in Linux or WSL:

```sh
make -C src -j4
python3 tools/test_look_optimization.py
python3 tools/test_clothing_optimization.py
python3 tools/test_description_optimization.py
python3 tools/test_expose_optimization.py
python3 tools/test_runtime_optimization.py
```

The focused tests use ASan/UBSan and instrumented production functions. The
runtime test uses a disposable world. Restart the server or debugger to load the
rebuilt executable.
