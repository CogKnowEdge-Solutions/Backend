# Lab 10 Assignment: Testing Endpoints with dependency_overrides

Complete these hands-on tasks after finishing the lab. You will write the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through Cell 16 first so the app, both dependencies, the
fake factories, and all four tests exist. After you edit a function or a
test, re-run its cell (and the cell that calls it) before checking the
result. Task 5 must be done last, since it leaves the endpoint without its
`safe` failure handling. Almost everything in these tasks runs on fake
clients (zero LLM cost); the only real model call is in Task 2's
wrong-key run.

---

### Task 1 — Failing on Purpose

In `test_unsafe_message_rejected_without_reply_call`, change the assertion
from `assert data["status"] == "rejected"` to `assert data["status"] ==
"approved"` — an intentionally wrong expectation.

1. Run the test.
2. Correct the assertion back to `"rejected"` and run it again.

- **Expected:** the first run stops with an `AssertionError` and never
  prints `PASSED` — the deliberate mismatch (the endpoint returns the
  rejected dict, but the test demands `approved`) is caught at the assert
  line. After the correction the test prints `PASSED`. This is the
  red/green rhythm a real test suite lives by: the failure tells you the
  assertion is actually being exercised.

---

### Task 2 — The Override With the Wrong Key

`app.dependency_overrides` is keyed on the **function object**, not the
function's name. Change the classifier override in test 2 from:

```python
app.dependency_overrides[get_classifier_client] = lambda: fake_classifier
```

to:

```python
app.dependency_overrides["get_classifier_client"] = lambda: fake_classifier
```

1. Run test 2 with the string key.
2. After the run, check `fake_classifier.call_count`.
3. Correct the key back to the function object and run test 2 again.

- **Expected:** with the string key the override silently does nothing —
  FastAPI resolves `Depends(get_classifier_client)` by looking up the
  function object, finds no entry, and falls back to the real classifier.
  The proof: `fake_classifier.call_count` is `0` (the fake was never
  invoked; the real model was called instead). The test's own pass/fail is
  now up to whatever the real model outputs, so don't rely on it — the call
  count is the decisive check. With the function-object key restored, the
  override takes effect, `call_count` is `1`, and the test prints `PASSED`
  deterministically against the fake.

---

### Task 3 — The Override That Must Hand Back a Callable

The override does not replace the classifier *value* — it is a dependency
callable that FastAPI **invokes with no arguments**, and whatever that
callable returns is what the endpoint receives as `classifier`. The
`lambda` is what makes it a callable that hands back the fake function. Try
storing something that is not a properly wrapped callable. Use test 1 for
each variation, starting from the working override:

1. **Bare function.** Store
   `app.dependency_overrides[get_classifier_client] = fake_classifier`
   (no `lambda`). FastAPI calls it with no arguments, but the function
   requires `message` → it throws during dependency resolution.
2. **Its return value.** Store
   `app.dependency_overrides[get_classifier_client] =
   fake_classifier("safe")` — evaluating the async function immediately
   produces a coroutine object (its body never runs), and a coroutine is
   not callable.
3. **Correct form.** Restore `lambda: fake_classifier` and run test 1 again.

- **Expected for step 1:** `response.status_code == 500` with the default
  `{"detail": "Internal Server Error"}` body — the `TypeError` fires inside
  FastAPI's dependency solver, before any endpoint logic. `fake_classifier.
  call_count` is `0`: the exception happens at argument binding, so the
  function body never executes.
- **Expected for step 2:** again `500` — the stored coroutine cannot be
  called as a dependency, so resolution fails the same way.
- **Expected for step 3:** `200`, status `approved`, and
  `fake_replier.call_count == 1`. The pattern to take away: the override
  must be *callable itself* (dependency-shaped), and what it *yields* must
  be the callable classifier — neither the bare function nor its return
  value satisfies both.

---

### Task 4 — A Fifth Test for "unknown"

The four tests cover `"safe"`, `"unsafe"`, a malformed value, and a raised
exception. Write a fifth test for a *plausible* never-seen case:

```python
def test_unknown_classification_rejected():
    fake_replier = make_fake_replier(response="This should never appear")
    fake_classifier = make_fake_classifier(response="unknown")
    app.dependency_overrides[get_classifier_client] = lambda: fake_classifier
    app.dependency_overrides[get_reply_client] = lambda: fake_replier
    response = test_client.post("/submit", json={"message": "Some message"})
    data = response.json()
    ...
```

1. Write the function, asserting `data["status"] == "rejected"`,
   `data["reason"] == "unrecognized classification"`, and
   `fake_replier.call_count == 0`.
2. Run it, then `app.dependency_overrides.clear()` afterwards — same as the
   other test cells.

- **Expected:** `PASSED`. The endpoint answers `"unknown"` the same way as
  `"maybe"` — anything that is not exactly `"safe"` fails closed before the
  replier is ever reached, so the replier's `call_count` stays `0`. You
  include the replier override as a safety net that proves that skip;
  without it the test would still pass, because the rejected path never
  resolves the replier dependency.

---

### Task 5 — Removing the Safety Net

The endpoint's `try/except` converts an upstream failure into a structured
`{"status": "error", "detail": ...}` response. Remove it so the endpoint
just calls the classifier directly (no `try`, no `except`), keeping the
rest of the body unchanged.

1. Edit the endpoint cell and re-run it.
2. Run test 4 (`test_classifier_failure_returns_clean_error`), and print
   `response.status_code` and `response.json()` after the call.

- **Expected:** the raised `RuntimeError("Classifier service unavailable")`
  is no longer caught. FastAPI's server-error middleware turns it into an
  HTTP `500` with the generic body `{"detail": "Internal Server Error"}`.
  The test's assertions now fail — there is no `"status": "error"` contract
  anymore. The difference is the whole point of the `try/except`: a `500`
  tells the client "the server broke," while the structured response tells
  it "this specific upstream service failed, here is exactly what happened."
  Leave the endpoint as-is once the behavior is confirmed.