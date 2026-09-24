# Lab 3 Assignment: Dependency Injection for AI Session Management

Complete these hands-on tasks after finishing the lab. You will write the
dependency functions and endpoint changes yourself — the instructions tell
you what to build and what result to check.

Run the notebook through Cell 7 first so `app`, `conversation_store`, and
`test_client = TestClient(app)` exist. After you add or edit a dependency,
re-run the edited cells plus the endpoint cell and the TestClient cell so
the running `app` picks up the changes before you test again.

---

### Task 1 — Counting Turns in the Response

Add a new dependency `get_turn_count(history: list = Depends(get_session))`
that returns `len(history)`. Inject it into `chat()` as an additional
parameter and include its value in the response under the key `turn_count`.
Then call `/chat` twice on the same session (a real message that succeeds):

- First call: **Expected** `turn_count` of `2` (one user message plus one
  assistant reply appended).
- Second call on the same session: **Expected** `turn_count` of `4`.
- The dependency must read the history that `get_session` yields, resolved
  before the endpoint body runs.

---

### Task 2 — Counting Only the User's Messages

Add a dependency `get_message_count` that also depends on `get_session` but
returns the number of messages whose `role` is `"user"` only — filtering
out the assistant replies. Inject it into `chat()` and return it under the
key `message_count`. Call `/chat` twice on a fresh session:

- First call: **Expected** `message_count` of `1`.
- Second call on the same session: **Expected** `message_count` of `2`
  (the assistant replies are counted out).
- Compare this with `turn_count` on the same two calls to confirm the
  difference: `2` vs `1`, then `4` vs `2`.

---

### Task 3 — Retrieving the Latest User Message

Add a dependency `get_last_user_message` that depends on `get_session` and
returns the `content` of the most recent message with `role == "user"`, or
`None` when there is none in the history. Scan the history in reverse so
"most recent" wins over earlier entries. Inject it into `chat()` and return
it under the key `last_user_message`. The dependency resolves before this
request's message is appended, so it reads the history as it was a moment
ago:

- Call on a brand-new session: **Expected** `last_user_message` is `None`.
- Second call on that same session: **Expected** it equals the message you
  sent on the first call — never the one you are currently sending.

---

### Task 4 — Breaking the Injection

The lab shows `client` arriving in `chat()` through
`Annotated[AsyncOpenAI, Depends(get_client)]`. Change the parameter so it
is declared as a plain `client` parameter *without* `Depends()` in its type
annotation, leaving everything else untouched, then call `/chat` with a real
message:

- **Expected:** the request no longer succeeds — FastAPI tries to treat the
  parameter as request data instead of resolving it, and you get a
  validation/parameter error rather than a working LLM call.

The point is to see with your own eyes that FastAPI only injects
a dependency when `Depends()` tells it to.