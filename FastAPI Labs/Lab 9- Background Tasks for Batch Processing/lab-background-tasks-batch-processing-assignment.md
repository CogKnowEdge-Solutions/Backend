# Lab 9 — Background Tasks for Batch AI Processing — Assignment

**Complete these exercises from the lab alone. You do not need to re-run the notebook.**

---

### Exercise 1 — What the Client Sees Before Any Work Starts (Concept)

After calling `POST /tasks/summarize-batch` with a list of 5 reviews, the client receives a response with `status: pending`. At the exact moment this response is constructed and returned to the client, has the background function `run_batch_summary` started executing? Has it set `status` to `running` yet? Explain why or why not, referring to how `BackgroundTasks` schedules work.

---

### Exercise 2 — Why `job_store` Must Be Module-Level (Concept)

The lab defines `job_store` as a module-level variable rather than creating it inside the POST endpoint function. If `job_store` were a local variable inside `summarize_batch`, what would happen when `run_batch_summary` tries to update `job_store[job_id]["completed"] += 1`? Would this work? Why or why not?

---

### Exercise 3 — Mid-Run Poll Behavior (Concept)

Suppose a batch of 4 reviews is being processed. The background task uses `job_store[job_id]["completed"] += 1` after each review is summarized. If a client polls the GET endpoint after the second review has finished but before the third starts, what value of `completed` will it see? What about `status`? Now suppose the `completed += 1` line were moved outside the loop to after it finishes entirely — how would the poll behavior change?

---

### Exercise 4 — What Happens Without Error Handling (Concept)

The `run_batch_summary` function wraps its loop in a try/except block. If this try/except were removed and the `simulate_failure` exception were raised instead, what would happen to the job's status in `job_store`? Would it remain `running` forever, become `done`, or something else? What would a client see if it polled the GET endpoint after this failure?

---

### Exercise 5 — Comparing Background Tasks to Streaming (Applied)

Lab 7 used `StreamingResponse` to send each chunk of an LLM response to the client as it was produced. Lab 9 uses `BackgroundTasks` to return a response before any LLM work happens. For a batch of 10 reviews that each take 3 seconds to summarize (30 seconds total), which approach is more appropriate and why? What problem would you encounter if you tried to use `StreamingResponse` for this batch scenario instead of `BackgroundTasks`?

---

## Answer Key

### Answer 1

No. At the moment the POST response is constructed and returned, `run_batch_summary` has not started executing at all. The response is built and sent to the client first — `background_tasks.add_task(...)` merely schedules the function to run later. FastAPI sends the response, then runs the background function. That is why `status` is still `pending` in the response: the background function that would set it to `running` has not yet begun.

### Answer 2

It would not work. `job_store` would be a local variable inside `summarize_batch`, created fresh each time the endpoint is called. The background function `run_batch_summary` runs in a separate context after the endpoint returns — it has no access to local variables from the endpoint. The background function would raise a `NameError` because `job_store` is not defined in its scope. A module-level variable is visible to all code in the file, which is why both the endpoint and the background function can read and write to it.

### Answer 3

The client would see `completed: 2` and `status: running` — the second review has finished and its result has been appended, but the third has not started yet. If `completed += 1` were moved outside the loop, the client would see `completed: 0` and `status: running` during the entire run (until the loop finished), then suddenly `completed: 4` and `status: done` on the next poll. Mid-run polls would show no progress at all, defeating the purpose of per-item updates.

### Answer 4

The exception would propagate up through the background task runner and the job's status would remain `running` forever — there would be no code path that sets it to `failed`. A client polling the GET endpoint would see the job stuck in `running` with `completed` stuck at whatever count it reached before the failure (in the case of `simulate_failure`, that would be `completed: 1`). The job would never transition to `done` or `failed`, so the client would have no way to know something went wrong. The try/except block explicitly catches the exception and sets the status to `failed` with a clear error message.

### Answer 5

`BackgroundTasks` is the appropriate choice. With `StreamingResponse`, the client must hold an HTTP connection open for the entire duration of the work — 30 seconds in this case. If the client disconnects, the work stops or becomes invisible. `BackgroundTasks` lets the client send the request, receive a job ID in milliseconds, and disconnect immediately. It can poll whenever it wants without holding any connection open. Additionally, `StreamingResponse` is designed for sending incremental output from a single generation — it does not naturally model "process N items sequentially and report progress after each one" the way a background task with a shared state dictionary does.
