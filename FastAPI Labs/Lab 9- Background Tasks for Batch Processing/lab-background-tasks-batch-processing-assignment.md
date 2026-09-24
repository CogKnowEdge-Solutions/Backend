# Lab 9 Assignment: Background Tasks for Batch Processing

Complete these hands-on tasks after finishing the lab. You will write all the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through your last demo first so `job_store`,
`run_batch_summary`, both endpoints, and the running server all exist. After
you edit a cell or add a new endpoint, re-run it before testing. Each task's
batch submits its own jobs; each review costs one (free-tier) LLM streaming
call, so a full pass of these tasks issues roughly 12–14 calls.

---

### Task 1 — Purging a Job From the Store

The lab's GET endpoint knows a job is gone from the "not found" fallback, but
nothing ever removes a job. Add `DELETE /tasks/{job_id}`:

1. Define the endpoint so it removes the job from `job_store` and returns a
   confirmation (e.g., `{"deleted": job_id}` or the removed job's state).
2. Submit a fresh batch, poll it until `done`, then DELETE it.
3. GET the same job ID afterwards.

- **Expected:** the DELETE returns a confirmation, and the following GET on
  that ID returns the same `{"error": ...}` "not found" message the lab
  returns for an ID that never existed. From the client's view, a deleted job
  and a never-existent job look identical — the GET's default-value lookup
  has nothing to fetch.

---

### Task 2 — The Disappearing Partial Progress

The lab places `job_store[job_id]["completed"] += 1` (and the results
append) inside the loop so mid-run polls show real progress. Move them out:

1. Take both lines out of the loop and run them **after** it instead, right
   before the status is set to `done`.
2. Submit a **batch of five** reviews and poll every second or two, printing
   `status` and `completed` each time, until the job is `done`.

- **Expected:** every poll that catches the job `running` shows
  `completed: 0` — there is no partial count and no partial results. The
  progress jumps straight to `5` only together with `status: done`. Exactly
  how many polls land mid-run depends on timing (a bigger batch widens the
  window), but during the run the numbers never climb by ones the way the
  lab's Demo 2 does.

---

### Task 3 — Two Flavors of One Endpoint

The timing demo proves the background POST returns in milliseconds — but what
would it cost to skip `BackgroundTasks` and just do the work inline? Define a
twin endpoint (e.g., `POST /tasks/summarize-batch-sync`) with the same
`BatchRequest` body, but instead of scheduling a task, run the exact same
summarize loop, `await`ing each call, and return the finished job state
directly (`status: done`, full `results`).

1. Add the endpoint; re-run its cell.
2. Time one POST to the **synchronous** twin and one POST to the original
   background endpoint, using `time.perf_counter()` around each, with the
   same three-review batch. Print both elapsed times and both response
   statuses.

- **Expected:** the background POST returns in a few milliseconds with
  `status: pending` (no summary work has happened yet — the old "timing
  proof" observation). The synchronous twin takes as long as the whole batch
  of LLM calls — several seconds — and its response already contains
  `status: done` and the full results, because the client could not get its
  answer until every review was summarized. The milliseconds-versus-seconds
  gap is what `BackgroundTasks` buys you, and it only grows with batch size.

---

### Task 4 — The Runaway That Never Finishes

The lab's `try/except` is what converts a failure into a clean `failed`
state. Remove the whole `try/except` from `run_batch_summary` (un-indenting
the loop) and submit a `simulate_failure=True` batch:

1. Remove the exception handling; re-run the cell.
2. Submit a three-review batch with `simulate_failure=True` and poll until
   you see the job can no longer change (the first review will still be
   summarized before the simulated failure on the second).

- **Expected:** the exception kills the background task; nothing ever sets
  the status again. The job stays `running` forever with `completed` frozen
  at `1` and no `error` field. FastAPI logs the failed background task to the
  server console, but the server itself keeps running. This is exactly the
  state the lab's `try/except` prevents — compare it with Demo 4's clean
  `failed` result from earlier.