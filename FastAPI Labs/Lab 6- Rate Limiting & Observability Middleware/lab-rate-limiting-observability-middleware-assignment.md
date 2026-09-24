# Lab 6 Assignment: Rate-Limiting & Observability Middleware

Complete these hands-on tasks after finishing the lab. You will write the
middleware and endpoint changes yourself — the instructions tell you what
to build and what result to check.

Run the notebook through Cell 6 first so `app`, `test_client`,
`rate_limit_store`, `RATE_LIMIT_WINDOW`, `RATE_LIMIT_THRESHOLD`, and the
middleware all exist. After you edit the middleware or add an endpoint,
re-run the edited cells. Note that the demos make real (free-tier)
OpenRouter calls, so each burst loop allocates a handful of LLM calls.

---

### Task 1 — Bug Hunt: the Wiped Window

The code-review bug resets a tenant's log on every request. Reproduce it on
the lab's sliding-window middleware:

1. Add this line to the middleware **inside** a `/chat` request, right after
   the store lookup:
   `rate_limit_store[tenant_id] = deque()`
   (leave everything else unchanged).
2. Re-run the Demo 2 burst loop.

- **Expected:** **no** 429s at all — every call returns `200`, no matter how
  fast the tenant fires. The tenant's timestamps are wiped before they are
  counted, so `len(window)` can never reach the threshold. The bug is not
  that a deque exists; it is *where* it is re-created.

---

### Task 2 — The Anonymous Tenant

The `/chat` endpoint identifies a tenant from the `X-Tenant-ID` header, and
`get_tenant_id` falls back to `"anonymous"` when the header is absent.

1. Send a `/chat` request with **no** `X-Tenant-ID` header at all.
   - **Expected:** HTTP `200` and the middleware's log line shows
     `tenant_id: "anonymous"` — the request is identified, not rejected.
2. Then fire several more header-less requests in a quick loop.
   - **Expected:** the `"anonymous"` bucket counts these calls too — it
     exhausts the threshold the same way any named tenant would, and you
     see a 429 whose log line names `"anonymous"`. This is why the fallback
     exists: unlabeled callers still consume *a* budget instead of skipping
     rate limiting entirely.

---

### Task 3 — Filling the Bucket with Tokens

Replace the sliding-window log rate limiter with a token-bucket rate
limiter:

1. Give each tenant a bucket holding up to `RATE_LIMIT_THRESHOLD` tokens
   (start full), and store the time the bucket was last refilled alongside
   it.
2. On each `/chat` request, refill the bucket from the elapsed time at a
   rate of 1 token per `RATE_LIMIT_WINDOW` seconds (cap at the capacity).
3. Require one token: if the bucket has one, consume it and let the request
   through; if it is empty, return the same 429 shape the lab uses.

Re-run Demo 1 and Demo 2 with your limiter:

- **Expected:** a single call consumes a token and succeeds; the burst loop
  still ends in 429s after the bucket drains (first two calls `200`, last
  two `429`).
- Re-run Demo 4 (the `RATE_LIMIT_WINDOW` sleep) — **Expected:** a token has
  refilled, so the next call succeeds. You are now throttling by
  *sustainable rate with burst tolerance* instead of *max requests per
  window*.

---

### Task 4 — Rate-Limiting a Second Route

The middleware currently rate-limits only `request.url.path == "/chat"`.
Extend it so any LLM-costing route is covered automatically:

1. Change the path check from equality on `"/chat"` to a membership test
   against a set of rate-limited paths (a constant like
   `RATE_LIMITED_ROUTES = {"/chat", "/summarize"}`).
2. Add a minimal `POST /summarize` endpoint that returns a small JSON
   payload (a plain, fast response is enough — the middleware's job is to
   throttle the *path*, not the endpoint's work).
3. Burst `/summarize` quickly from `tenant-a`, then immediately call
   `/summarize` from `tenant-b`.

- **Expected:** `tenant-a` hits the threshold and starts receiving `429`s
  on `/summarize` (with the same no-usage log lines), while `tenant-b`
  succeeds — the new route is throttled per tenant *because it was added to
  the set*, with zero changes inside the endpoint. This is the middleware's
  whole advantage over a `Depends()` kept inside `/chat` alone.

---

### Task 5 — Advertising the Requests Remain

Add a response header so clients can see how much budget they have left.
In the middleware's post-response section (after the rate-limit check,
before returning the response), set a `X-RateLimit-Remaining` header equal
to the number of requests the tenant still has — for the sliding-window
limiter that is `max(0, RATE_LIMIT_THRESHOLD - len(window))`; with the
token-bucket limiter, use the bucket's current token balance. For a
non-rate-limited route, you may skip it.

- Test it: fire calls in a rapid loop for one tenant and print
  `res.headers.get("X-RateLimit-Remaining")` each time.
  - **Expected:** the value counts down from the threshold toward `0`, and
    the `429` response itself carries `X-RateLimit-Remaining: 0`.