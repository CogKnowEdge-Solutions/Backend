# Lab 1 Assignment: Pydantic Validation for AI Request/Response Contracts

Complete these hands-on tasks after finishing the lab. You will write the
schema changes and request payloads yourself — the instructions tell you
what to build and what result to check.

Run the lab notebook through Cell 9 first so `app` and
`client = TestClient(app)` exist. After you edit a schema or dictionary
cell, re-run that cell, then re-run the endpoint cell and the TestClient
cell so the running `app` picks up the change.

---

### Task 1 — Bounding `top_p` at the Request Boundary

Add a new required field `top_p: float` to `ChatRequest`, bounded between
0 and 1 inclusive using `Field`'s bound keywords — the same constraint
pattern the lab applies to `temperature`. Send a request to `/chat`
through `TestClient` that carries `top_p=1.5` while every other field stays
within its valid bounds. You should receive HTTP 422, and the validation
detail must name `top_p` as the failing field. Note that once `top_p` is
part of the schema it is required: every payload in the tasks below must
include a valid `top_p` value (between 0 and 1) or it will 422 for a
missing field.

---

### Task 2 — Rejecting an Unknown Message Role

Post a request through `TestClient` whose `messages.role` is a string
outside the two values allowed by the `Message` schema — keep `temperature`
and `max_tokens` (plus `top_p`, if you completed Task 1) inside their valid
bounds so the role is the only violation. You should receive HTTP 422, and
the error's `loc` must point at `messages, role`, proving the nested
`Message` schema rejected the payload before the endpoint code ran.

---

### Task 3 — Tightening `max_tokens` to a Closed Range

In `ChatRequest`, replace the current `max_tokens` constraint (`Field(gt=0)`)
with a closed range that accepts only 1 through 2048 inclusive — use the
same inclusive-bound keywords the lab uses for `temperature`. Verify both
edges through `TestClient`: a payload with `max_tokens=0` and a payload
with `max_tokens=2049` must each return HTTP 422 citing `max_tokens`, while
an in-range value such as `150` returns HTTP 200 for the lab's France
question.

---

### Task 4 — Extending the Mock LLM with a New Capital

Add one new entry to `MOCK_REPLIES` keyed by the exact question text
`What's the capital of Italy?`, with an `assistant` reply whose `content`
answers the question and satisfies `ChatResponse`'s minimum-length rule.
Then POST the matching single-message payload through `TestClient` — `role`
`user`, the same question text as `content`, and all numeric fields within
their valid bounds. You should receive HTTP 200 with your Italy reply in the
response JSON. The mock lookup only matches when the request `content`
equals the dictionary key character for character, so double-check the key
and the payload if you get an empty or failing response.
