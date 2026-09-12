# Runtime hardening and social matching

Social updates build temporary, case-insensitive profile and unordered name-pair
indexes. They retain the first matching vector entry and rebuild each update, so
profile edits and reordering need no persistent cache invalidation. Meeting
eligibility is evaluated once per pair. The existing descriptor order and random
selection calls are retained. `HAVEN_PROFILE=1` now includes `social_update` timing;
production latency improvements have not yet been measured.

An ignored chat invitation clears its pending initiator when its success/failure
outcome is applied. Later updates cannot score it again. Login rating prompts
also tolerate a counterpart profile that has expired.

Socket output retains unsent bytes on EAGAIN/EWOULDBLOCK and retries EINTR. Each
flush sends at most 64 KiB. Retries do not duplicate prompts or snooped text.
Pending output is capped at 1 MiB; overflow disconnects the client on the output
pass rather than freeing a descriptor during a gameplay callback. Socket buffers
use the heap because their maximum exceeds the game allocator's largest bucket.

Note text and board strings are read into `std::string`. Array-based word/string/
line reads infer their capacity, reject overflow, and set an error state. Missing
terminators and incomplete note records fail loading without dereferencing null.
Formatted output allocates enough space when its stack buffer is insufficient;
numeric output accommodates the full signed/unsigned long range.

## AI queues and deployment

AI processing is **disabled by default** in both the game and Python worker.
Only the exact environment value `HAVEN_ENABLE_AI=1` enables it. Leave the
variable unset (or set it to `0`) while AI is unused. Restart the game and stop
any old worker to apply this change to running processes.

While disabled, the game skips periodic AI jobs, social scoring, generated doom,
operative generation and result polling. It leaves queue contents, cursors and
report sent flags untouched. Commands that need generation report that it is
disabled; existing saved operatives and manually supplied doom still work.
The Python worker exits before importing optional packages, opening logs or
queues, or contacting any service.

To re-enable later, set `HAVEN_ENABLE_AI=1` in **both** launch environments and
restart them. The worker also reads `OPENAI_API_KEY` and, optionally,
`OPENAI_ORGANIZATION`; its existing optional packages are required when enabled.
Retained requests and results resume from their saved cursors. Summary results
now go to `ai_sum_out.csv`, matching the game, with one append per result. Any
historical `ai_sum_out.tmp` file is left untouched.

Deploy the updated executable **before starting the updated Python worker**.
Stop the old worker during this change, and copy both `src/run_ai_engine.py` and
`src/ai_queue.py` together. The executable still accepts valid legacy `|||`
responses, while the new worker emits escaped JSON arrays, one per physical line.
Generated newlines, quotes and delimiters remain inside their fields. Both sides
validate field counts, numeric ranges, names and text sizes before publishing or
applying a result. Operation results include territory, faction and battleground
identity; ambiguous legacy responses are ignored rather than applied to several
operations. Player/world save formats are unchanged.

Input queues remain CSV, with stable `<queue>.lock` files shared by C++ producers
and the Python consumer. Summary producers append one complete quoted record,
including all report continuation pages, and set their sent flag only after a
successful durable append. Failed partial appends are rolled back while locked.
An empty/missing input queue receives its header on the first C++ append.

The worker holds a separate `<queue>.worker.lock` while processing and releases
the producer lock before calling AI or website services. It commits a small
`<queue>.worker-cursor` after each successful request. Failed requests retry on
the next pass; after five failures their fields and error are retained in
`<queue>.failed.jsonl` before the cursor advances. Each pass reads at most 32
requests and coalesces identical successful rows within that pass. Acknowledged
prefixes compact after 1 MiB when they occupy at least half the queue.

Execution is at least once: a crash after a side effect but before cursor commit
can replay that request. This is not an exactly-once transaction across the game,
AI provider and website. The result consumer retains its existing acknowledgement
before gameplay dispatch. Do not delete live cursors or truncate/refill the same
inode; for restoration, stop the worker and restore an unread suffix with its CSV
header in a replacement file. Failed records should be inspected before requeueing.

## Verification

Run in Linux/WSL from the repository root. Tests use temporary files and do not
call AI providers or modify live saves.

```sh
make -C src -j4
python3 tools/test_ai_queue.py
python3 tools/test_runtime_hardening.py
python3 tools/test_runtime_optimization.py
python3 tools/test_memory_safety.py
python3 tools/test_command_dispatch.py
make -C src BUILD=debug SANITIZE=1 -j3 .build-local/debug-sanitize1/haven
python3 tools/test_runtime_hardening.py --sanitize
python3 tools/test_memory_safety.py --sanitize
```

Building the explicit sanitizer cache target leaves the installed release
executable unchanged. The focused tests cover long notes/output, numeric bounds,
partial socket writes and closed peers, social lookup/order equivalence and
invitation outcomes, malformed AI payloads, operation identity, concurrent queue
arrivals, worker restarts, retries, quarantine and compaction recovery.
