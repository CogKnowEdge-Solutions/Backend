# Lab 7 Assignment: Streaming Responses with SSE for AI Chat

Complete these hands-on tasks after finishing the lab. You will write the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through Cell 5 first so `app`, `http_client`, and
`stream_tokens` all exist and the server is running on `PORT`. After you
edit the generator or an endpoint, re-run those cells before testing again.
The tasks make real (free-tier) OpenRouter calls, so each demo run costs a
handleful of small generations.

---

### Task 1 — Twisting the Interruption Threshold

The lab's generator stops a simulated failure with
`simulate_error and event_count >= 2`: after two content chunks it yields
`event: error` and returns. Change that number and re-run Demo 4's client
loop (`simulate_error=True`) after each edit, watching how many
`event: token` lines appear before `event: error`:

- **Threshold `0`:** the error fires on the very first content chunk.
  - **Expected:** zero `event: token` lines before `event: error`.
- **Threshold `999`:** the error branch is never reached.
  - **Expected:** the stream runs to completion and ends with `event: done`
    instead — the error only fires when the stream is still producing chunks
    past the threshold.
- **Threshold `5`:** either outcome is valid — if the model emits at least 5
  chunks you see 5 tokens then the error; if `openrouter/free` delivers
  fewer, larger chunks the loop ends first and you see `event: done`. Observe
  whichever happens; both confirm how the interruption condition interacts
  with the number of chunks the provider actually sends.

---

### Task 2 — Counting the Words as They Stream

The generator already tracks how many `event: token` events it has sent in
`event_count` (incremented each time a content chunk is yielded). Add one
more SSE event that reports that total before the stream closes:

1. Yield `event: wordcount` with `data:` carrying `event_count`.
2. Place it **after** the chunk loop finishes (so the count is final) and
   **before** the `event: done` yield, so `done` stays the last event the
   client receives.

Consume a normal stream (`simulate_error=False`) and check the event
sequence:

- **Expected:** the `wordcount` event arrives as the second-to-last event,
  and its value equals the number of `event: token` lines you received
  (the empty-delta chunks are already skipped by the existing
  `if delta.content:` guard, so the count tracks real text only).

---

### Task 3 — Why `.stream()` Not `.post()`

Demo 2 measures "time to first output" using `http_client.stream()`. Run a
controlled comparison to see what the alternative does:

1. Time a call to `/chat/stream` using `http_client.post()` instead
   (`start = time.perf_counter()` just before, stop once it returns).
2. Run the same prompt through `http_client.stream()` (or reuse Demo 2's
   recorded first-output time).

- **Expected:** the `post()` elapsed time is close to the stream's *full*
  completion time, not its first-output time — noticeably larger than the
  `.stream()` first-output measurement. A plain `post()` reads the entire
  response body into memory before returning, so your code cannot see the
  first line until every chunk (including `event: done`) has arrived;
  `.stream()` exposes each chunk as it arrives, which is the only way to
  time the first output honestly.

---

### Task 4 — The Too-Late Try/Except: Raising Mid-Stream

One common instinct is to "just catch the error and return a 500 JSON
response". This task shows why that cannot work once streaming has begun.

In `stream_tokens`, the simulated-failure branch currently yields a clean
`event: error` then returns. Instead, remove that yield/return and let the
generator fail with a bare `raise RuntimeError("Stream broke")`, leaving
everything else the same. Re-run Demo 4's client loop
(`simulate_error=True`):

- **Expected:** the stream stops abruptly. You never receive an
  `event: error` line, and no `event: done` follows — the client loop
  simply ends early, or a client-side exception surfaces. There is no
  structured error body at all.

The reason is timing: by the time a chunk has been sent, the HTTP status
code and headers (including `200`) are already committed to the client.
Nothing can retroactively swap them for a 500. A failure that happens after
streaming starts can only travel *inside the stream* as an SSE event —
exactly what the clean `event: error` yield in the working version does.