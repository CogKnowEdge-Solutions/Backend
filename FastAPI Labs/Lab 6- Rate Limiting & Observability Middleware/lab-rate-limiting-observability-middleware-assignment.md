# Lab 6 — Rate-Limiting & Observability Middleware — Assignment

**Complete these exercises from the lab alone. You do not need to re-run the notebook.**

---

### Exercise 1 — Middleware vs. Dependency (Concept)

In the lab, tenant identity is read from the `X-Tenant-ID` header both by the `get_tenant_id` dependency (used by the `/chat` endpoint's session history) and by the middleware (used for rate-limit counting). Why would it be a poor design to put the *entire* rate-limiting logic inside a dependency like `get_tenant_id` instead of in the middleware? Name one specific consequence for a route added after the fact.

---

### Exercise 2 — Sliding Window vs. Fixed Window (Concept)

A fixed-window rate limiter counts requests in a clock-aligned window (e.g., 00:00–00:45, 00:45–01:30). Describe a specific scenario where a client can make 6 requests in a short span while a "3 requests per 45 seconds" limit is in effect (matching this lab). Then explain why the sliding window log used in this lab cannot be exploited the same way.

---

### Exercise 3 — The Missing-Header Case (Concept + Code)

The `/chat` endpoint is called with no `X-Tenant-ID` header at all. Trace what happens: what tenant ID does the request get scoped to, does the request succeed or get rejected, and why is this described as an "identification fallback" rather than an "authentication rejection"?

---

### Exercise 4 — What request.state Solves (Concept)

The `/chat` endpoint passes LLM usage data to the middleware via `request.state.usage`. Why can't the middleware simply read this data from the endpoint's return value (the JSON response body)? Name one specific problem with that approach.

---

### Exercise 5 — Expanding Rate Limits to Other Routes (Applied)

The middleware currently checks `if request.url.path == "/chat"` to decide whether to rate-limit. If you wanted to also rate-limit a hypothetical `POST /summarize` endpoint (which also makes an LLM call), what specific change(s) would you make to the middleware? Do not write the full implementation — just describe the change concisely.

---

### Exercise 6 — Adding a Remaining-Requests Header (Short Code)

Write a Python snippet (3–5 lines, not a full function) that could be added to the middleware's post-response section to set a `X-RateLimit-Remaining` response header showing how many requests the tenant has left in their current window. Assume `window` is the deque of timestamps for the tenant and `RATE_LIMIT_THRESHOLD` is the max allowed.

---

### Exercise 7 — Reading the Log Line (Concept)

List every field that appears in the middleware's structured log line for (a) a successful `/chat` call and (b) a rejected 429 call. What is the one difference between the two lines, and why does it exist?

---

### Exercise 8 — Identifying a Bug (Code Review)

The following is a hypothetical modification to the rate limiter. Identify the bug and explain why it fails to actually throttle requests:

```python
# Hypothothetical buggy code — NOT from the lab
if tenant_id not in rate_limit_store:
    rate_limit_store[tenant_id] = deque()

rate_limit_store[tenant_id] = deque()

window = rate_limit_store[tenant_id]
while window and window[0] <= now - RATE_LIMIT_WINDOW:
    window.popleft()

if len(window) >= RATE_LIMIT_THRESHOLD:
    return JSONResponse(status_code=429, ...)
window.append(now)
```

---

### Exercise 9 — Production Rate Limiter Design (Applied)

The lab's rate limiter stores timestamps in a Python dict (single-process, in-memory). Describe two specific problems this causes in a production deployment with 4 worker processes behind a load balancer, and name one external store (e.g., Redis) that solves each problem.

---

## Answer Key

### Answer 1

The middleware is the natural home for a concern that must apply to *every* route. If the rate-limiting logic lived in a dependency, it would only run for routes that explicitly declare that dependency. A new route (like a future `POST /summarize`) added without remembering to attach the dependency would be completely unthrottled — an accidental, un-limited LLM-cost hole. The middleware applies to all routes automatically, so a concern that must be universal (or must run before any endpoint) belongs there, not in a per-endpoint dependency.

### Answer 2

**Fixed-window exploit:** Suppose the window resets at :00 and :45 seconds. The client sends 3 requests at 00:44:59 (within the first window, count = 3, all allowed). Then 3 more requests at 00:45:01 (within the second window, count = 3, all allowed). That is 6 requests in about 2 seconds, exceeding the intended limit of "3 per 45 seconds."

**Why sliding window avoids this:** The sliding window log always looks back over a rolling 45-second period from *now*, not from a clock boundary. At 00:45:01, the window includes requests from 00:44:16 to 00:45:01 — the 3 requests from 00:44:59 are still inside that window, so the count is 6, which exceeds the threshold, and the 4th request is rejected. There is no boundary to straddle.

### Answer 3

When no `X-Tenant-ID` header is sent, `get_tenant_id` returns its default value `"anonymous"`, so the request is scoped to the `"anonymous"` tenant. The request **succeeds** — there is no authentication layer in this lab to reject it. This is an *identification* fallback, not an *authentication* rejection: the system simply assigns a default identity so rate-limit counting can still happen for unlabeled callers. A header is not a security boundary, and this lab makes no security claim — it only reads an identifier for accounting.

### Answer 4

The middleware wraps the entire request/response cycle — it calls `await call_next(request)` and gets back a *response object* (a `StreamingResponse` or `JSONResponse`), not the Python return value of the endpoint. The response body is the serialized JSON (e.g., `{"answer": "...", "history": [...]}`), which is a stream, not parsed data. To read the body, the middleware would have to consume the stream — which might break the response for the client. `request.state` is the clean, purpose-built channel for endpoint-to-middleware communication that avoids this problem entirely.

### Answer 5

Replace the single path check with a set of rate-limited paths:

```python
RATE_LIMITED_ROUTES = {"/chat", "/summarize"}
if request.url.path in RATE_LIMITED_ROUTES:
    # ... rate-limit logic
```

This keeps the middleware's cost-control scope explicit and makes it trivial to add new LLM-calling routes later.

### Answer 6

```python
remaining = max(0, RATE_LIMIT_THRESHOLD - len(window))
response.headers["X-RateLimit-Remaining"] = str(remaining)
```

This goes after the rate-limit check and before `return response`. It tells the client exactly how many more requests they can make in the current window.

### Answer 7

For a successful call, the log line carries: `tenant_id`, `path`, `status_code`, `latency_ms`, `prompt_tokens`, `completion_tokens`, and `total_tokens`. For a rejected 429 call it carries only: `tenant_id`, `path`, `status_code`, and `latency_ms` (≈ 0.0).

The difference is the three token-usage fields. They are only set when the middleware finds a `request.state.usage` on the request — and that is only written by the endpoint after a real LLM response. On a 429 the middleware returns before the endpoint ever runs, so no usage data exists and the fields are simply absent. The missing fields are therefore the proof that a billed LLM call never happened.

### Answer 8

The bug is the line that reassigns `rate_limit_store[tenant_id] = deque()` on **every** request. It wipes the tenant's stored history before the count happens, so the count is always taken against an empty deque. `len(window)` is always 0, which is always `< RATE_LIMIT_THRESHOLD`, so the limiter never returns 429 — **no request is ever throttled**, regardless of how fast the tenant sends them. The correct code, as in the lab, creates the deque only when the tenant is first seen (`if tenant_id not in rate_limit_store:` then initialize), and never overwrites it afterward.

### Answer 9

**Problem 1 — No shared state across workers:** Each worker has its own dict. A tenant sending requests that hit different workers will have separate rate-limit counters, allowing them to exceed the per-tenant limit. Redis solves this by providing a single, shared store that all workers query and update.

**Problem 2 — State lost on restart:** If a worker process restarts (e.g., crash, deployment), its in-memory dict is wiped and all rate limits reset. A tenant who was throttled immediately gets a fresh quota. Redis persists the data independently of the application process, so rate-limit state survives restarts.
