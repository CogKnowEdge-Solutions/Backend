# Lab 2 Assignment: Exception Handling In FastAPI

Complete these hands-on tasks after finishing the lab. You will write the
exception classes, handlers, and endpoint changes yourself — the instructions
tell you what to build and what result to check.

Run the notebook through Cell 9 first so `app` and `test_client = TestClient(app)`
exist. After you add an exception class or edit the endpoint, re-run the edited
cells — plus the endpoint cell and the TestClient cell — so the running `app`
picks up the changes before you test again.

---

### Task 1 — Rejecting an Empty Prompt Before the API Call

Add a new custom exception `LLMEmptyMessageError` (a plain `Exception`
subclass) and register a matching `@app.exception_handler()` that returns
HTTP `400 Bad Request` with a short JSON error body explaining that the
message is empty. Raise the exception at the very top of `chat()`, before
any OpenRouter client is created, when `message` is an empty string. Test
it by posting to `/chat` with `message=''`:

- **Expected:** HTTP `400` and your error JSON in the body.
- This check runs before the API call, so it works even without a valid
  API key.

---

### Task 2 — Rejecting an Overlong Prompt Before the API Call

Add a second custom exception `LLMTooLongMessageError` and its own
`@app.exception_handler()` that returns HTTP `413 Payload Too Large` with a
clear error message about the length limit. Raise it at the top of `chat()`,
next to the empty-message check, when the message is longer than 500
characters (use `len(message)` for the count). Test it by sending a
501-character message:

- **Expected:** HTTP `413` with your error JSON in the body.
- Set the threshold strictly: a 500-character message must pass this check,
  a 501-character message must not.

---

### Task 3 — A Quota Failure Wired Through a New Flag

Define a third custom exception `LLMQuotaExceededError` representing an
exhausted daily quota, and register a handler that returns HTTP
`429 Too Many Requests` with a JSON body containing an `error` key with the
value `quota exceeded` and a short `message` describing the quota being
exhausted. Wire it into the endpoint:

- Add a boolean query parameter `quota_exceeded: bool = False` to `chat()`.
- Raise `LLMQuotaExceededError()` at the start of the endpoint when that
  parameter is `True` — before any OpenRouter call, like the length checks.

Test it by posting to `/chat` with `quota_exceeded=True` (any non-empty
`message`):

- **Expected:** HTTP `429` with `{"error": "quota exceeded", ...}` in the body.
- This mirrors the lab's flag pattern (`deprecated_model`, `bad_key`, etc.)
  applied to a failure the lab did not cover.

---

### Task 4 — Centralizing API Status Errors at the App Level

In the lab, `chat()` classifies `APIStatusError` locally: it checks
`e.status_code` inside the `try/except` and raises a custom error (or returns
a fallback) from there. Move that classification out of the endpoint:

- Delete the `except APIStatusError` branch from `chat()`.
- Register `@app.exception_handler(APIStatusError)` on the app and reproduce
  the same branching inside the handler:
  - status `400` → raise/return the `BadModelError` response shape (HTTP `404`,
    `error` about an invalid model).
  - status `401` → the auth error shape (HTTP `401`, `error` about
    authorization).
  - any other status → HTTP `502` with an `error` key describing an upstream
    failure.
- Leave the `asyncio.TimeoutError` handling in `chat()` unchanged. The
  endpoint should only raise custom exceptions from now on.

Verify the behavior is unchanged by calling the existing failure flags:

- **Expected:** `deprecated_model=True` still returns HTTP `404`, and
  `bad_key=True` still returns HTTP `401`, with the same error bodies as in
  the lab — but now produced by the app-level handler instead of the local
  `except`.