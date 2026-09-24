# Final Grading Quiz — FastAPI for AI Applications

This quiz covers the FastAPI concepts taught across Labs 1-12 (Lab 13 is
excluded). It contains 20 multiple-choice questions: 5 Easy, 10 Medium,
5 Intense. Each question has exactly one correct answer. Questions are
grouped by topic for navigation, but every question tests the underlying
FastAPI concept — not how a specific lab was built. Scenario-based and
cross-concept comparison questions are included where they best test
understanding. Answers and short explanations are in the Answer Key at the
end of this file. An import-ready version following
`QuestionsImportTemplate-v4.xlsx` is available as `FINAL_GRADING_QUIZ.xlsx`.

## Pydantic Validation

**Q1.** [Easy] What HTTP status code does FastAPI return by default when a client's request
body fails Pydantic validation?

- A. 422 Unprocessable Entity
- B. 400 Bad Request
- C. 404 Not Found
- D. 500 Internal Server Error

**Q2.** [Medium] An AI service validates the LLM's reply against a Pydantic model before
returning it to the caller. What is the main reason for this outbound validation?

- A. To prevent an LLM response from exceeding the model's maximum token limit in a single turn.
- B. To guarantee the request schema and the response schema are exactly identical in shape.
- C. To catch occasional malformed or empty LLM output before it corrupts downstream consumers.
- D. To strip personally identifiable information from the reply before it leaves the service.

---

## Async Execution

**Q3.** [Easy] When should a path operation be declared with plain `def` instead of `async
def` in FastAPI?

- A. When it needs to call an async client library and `await` its results directly instead of blocking on the result.
- B. When it does CPU-bound work that would block the event loop and is faster in a threadpool.
- C. When it must stream a large file or a response body back to the client in many chunks.
- D. When its inputs come from `Path`, `Query`, and request-body parameters in the signature.

**Q4.** [Medium] Inside an `async def` endpoint, why does `await` in a sequential loop NOT
produce concurrency, while `asyncio.gather()` does?

- A. Because `await` blocks the entire event loop until the awaited call returns, stalling other requests.
- B. Because `gather()` parallelizes calls by spawning extra worker threads under the hood.
- C. Sequential awaits add their times up; `gather()` overlaps them so the total is about the slowest.
- D. Because `gather()` creates a separate event loop for each call, letting the calls truly run in parallel.

---

## Exception Handling

**Q5.** [Medium] What is the key difference between a local `try/except` block and an
`@app.exception_handler(ExceptionType)`?

- A. A local `try/except` catches only errors inside its block; an app-level handler catches the type app-wide.
- B. A local `try/except` block always runs on a separate thread, away from the event loop.
- C. `@app.exception_handler` can only handle exceptions shipped in Python's standard library, never exceptions you define in your own project.
- D. They behave identically; the decorator is syntactic sugar over a `try/except`.

**Q6.** [Intense] You register `@app.exception_handler(MyError)` and also wrap the endpoint
body in `try/except MyError`. An exception `MyError` is raised inside the endpoint. Which
handler responds to the client?

- A. The local `except` catches it first; the handler only fires if the exception escapes the block.
- B. The `@app.exception_handler` always runs instead of the local clause, so the local one never fires.
- C. The registered handler runs first; the local `except` only acts after the handler returns control.
- D. The request fails with a 500 because the two handlers conflict over the same exception.

---

## Dependency Injection

**Q7.** [Easy] What does FastAPI inject when an endpoint parameter is declared with
`Depends(get_client)`?

- A. The `get_client` function object itself, passed to the endpoint by reference.
- B. A brand-new client object that is constructed afresh on every single request.
- C. The HTTP `Request` object belonging to the current call, including its headers and path.
- D. The return value of `get_client()`, resolved by FastAPI before the endpoint runs.

**Q8.** [Medium] In a yield-dependency structured as `try: yield history` / `finally:
print("done")`, when does the `finally` block run?

- A. After the endpoint finishes, whether it succeeded or raised an exception.
- B. Immediately after the `yield`, before the endpoint body ever runs.
- C. Only when the endpoint raises an unhandled exception and the request fails.
- D. Only on those requests that complete successfully without any error.

---

## Security (OAuth2 + JWT)

**Q9.** [Easy] What does `OAuth2PasswordBearer(tokenUrl="/token")` actually do when used as
a dependency on a protected route?

- A. Verifies the token's cryptographic signature and its expiry against the JWT secret.
- B. Extracts the raw bearer token from the Authorization header, rejecting a missing header.
- C. Looks up the user's account in the database to confirm that it exists and is active.
- D. Decodes the bearer token into its individual JWT claims for the endpoint to consume.

**Q10.** [Medium] A route must reject a request carrying an invalid JWT with 401 before the
endpoint logic runs. What is the FastAPI-native mechanism for this?

- A. A middleware that decodes the token before routing, so invalid tokens never reach the handler.
- B. Declaring the OAuth2 security scheme inside the app's OpenAPI schema so that clients know exactly how to authenticate.
- C. A catch-all exception handler registered at app level that turns every token error into a 401.
- D. An endpoint dependency like `Depends(get_current_user)` that runs first and raises 401 on an invalid token.

**Q11.** [Intense] A stateless JWT contains the claims (e.g., `tenant_id`, `exp`) in a
signed token, and the server has no server-side session store. How does the server know the
request is legitimate on every call?

- A. The signature proves the token was issued by the server and untampered, so the claims are trusted without any lookup.
- B. It queries the database on every request to confirm the user's account is still active and has not been disabled or revoked.
- C. It trusts the client's claims as-is because they arrived over an encrypted HTTPS connection.
- D. It stores every issued token in an in-memory cache and validates each request against it.

---

## Rate Limiting & Middleware

**Q12.** [Medium] Why is rate limiting for a paid LLM API placed in middleware that runs
BEFORE the endpoint executes, rather than checked after the endpoint returns?

- A. Because middleware cannot read the request headers once the endpoint has already responded.
- B. Because dependency checks only run after the endpoint has already finished executing its work.
- C. Because checking the limit after the endpoint has run is technically impossible in FastAPI.
- D. Because a throttled request is rejected before the paid LLM call is ever made.

---

## Streaming with SSE

**Q13.** [Medium] In Server-Sent Events (SSE), what is the role of the empty blank line
between events?

- A. An optional keep-alive heartbeat that keeps the connection from idling out.
- B. Whitespace that SSE parsers ignore completely, like indentation in plain text.
- C. The delimiter that marks the end of one event and the start of the next.
- D. The signal that the server has finished and the stream is now ended.

---

## WebSockets & Full-Duplex Communication

**Q14.** [Medium] An operator dashboard must show live, read-only updates - for example
streaming token usage or log lines - pushed from the server as soon as they occur. Clients
never send anything back. Which architecture is the best fit?

- A. REST - the browser polls `/updates` on an interval and diffs each response against the last one.
- B. WebSockets - a full-duplex persistent connection over which browser and server exchange messages freely.
- C. HTTP long-polling - each request stays open until new data arrives, at which point the client reconnects for the next update.
- D. Server-Sent Events (SSE) - a one-way HTTP stream the server pushes to the browser with automatic reconnection.

**Q15.** [Intense] You need the client to be able to send messages to the server AT ANY
TIME, even while the server is mid-response (e.g., a Stop button or a follow-up). Which
technology fits, and why?

- A. SSE - keeps an HTTP connection open and delivers each update to the browser as the server produces them.
- B. Plain HTTP - each request is independent, and the protocol is naturally full-duplex.
- C. WebSockets - after the upgrade handshake, both sides freely send data over one persistent connection.
- D. Server polling - the client repeatedly polls a message queue that the server fills on its behalf over time.

---

## Background Tasks

**Q16.** [Easy] An endpoint hands a slow, multi-minute job to `BackgroundTasks` and returns
a response immediately. What does the client receive right away?

- A. The completed job results from the background work, delivered once it finishes processing.
- B. A confirmation/job ID; the actual work runs after the response is sent.
- C. Nothing - the connection just stays open until the whole job finishes.
- D. An HTTP 504 Gateway Timeout because the job ran longer than expected.

---

## Testing

**Q17.** [Medium] What does `app.dependency_overrides[get_classifier_client] = lambda:
fake_classifier` accomplish?

- A. It deletes the classifier dependency from the app so the endpoint no longer needs one.
- B. It swaps the dependency by function object so the endpoint gets the fake with zero endpoint changes.
- C. It replaces the classifier with the fake for requests that send a special HTTP header on each call.
- D. It permanently rewrites the endpoint's behavior in production environments when deployed.

**Q18.** [Intense] A test overrides `get_classifier_client` via `app.dependency_overrides`
but never clears the overrides dictionary afterward. What happens when a later test runs
against the same app?

- A. FastAPI resets the overrides automatically as soon as the test function returns.
- B. The app raises an error because only a single override may be registered at one time.
- C. The override applies only to the very first request that the app ever serves.
- D. The override silently persists, so the later test keeps using the fake without noticing.

---

## Modular Routing

**Q19.** [Medium] A dependency is passed at `APIRouter()` construction time in
`dependencies=[Depends(check)]`. When does it run?

- A. Only on the very first mount of the router object, across its whole lifetime.
- B. Only on endpoints that explicitly import the function and depend on it inside their own signature.
- C. On every request to that router's routes, at every mount, since it is baked into the router.
- D. Only once, at import time, when the router object itself is created and mounted.

---

## Cross-Concept: Middleware vs Depends vs Lifespan

**Q20.** [Intense] A cross-cutting concern must apply to EVERY request to EVERY route (e.g.,
logging), AND some expensive resource must be loaded exactly ONCE for the whole app (e.g.,
an embedding model). Which pairing handles them best?

- A. A `Depends()` hook for the logging, plus a per-request cache that loads the model every call.
- B. An `@app.middleware("http")` for the logging and a lifespan that loads the model once onto `app.state`.
- C. Two separate `Depends()` functions, one dedicated to each concern, applied per route.
- D. Load the model lazily inside every route handler that happens to need it, on first use per request.

---

## Answer Key

| No. | Answer | Difficulty | Topic | Explanation |
|-----|--------|------------|-------|-------------|
| 1 | A | Easy | Pydantic | FastAPI validates the request body against the declared schema and returns 422 Unprocessable Entity on failure. |
| 2 | C | Medium | Pydantic | LLMs are non-deterministic and may violate schemas; outbound validation protects downstream systems from corrupt data. |
| 3 | B | Easy | Async | CPU-bound code never awaits, so inside an `async def` handler it would hold the event loop hostage; declaring the handler with plain `def` tells FastAPI to run it in a threadpool, leaving the event loop free for other requests. |
| 4 | C | Medium | Async | Sequential awaits sum the times; `gather()` starts all awaits before waiting, so total time is roughly the slowest call. |
| 5 | A | Medium | Exceptions | A `try/except` only catches within its block; an app-level handler catches the type anywhere in the lifecycle. |
| 6 | A | Intense | Exceptions | A local `except` runs first if it matches; the app-level handler fires only when the exception propagates past local handling. |
| 7 | D | Easy | Depends | FastAPI resolves the dependency before the endpoint runs and injects its return value as the parameter. |
| 8 | A | Medium | Depends | The `finally` block runs after the endpoint completes, success or failure - the guarantee yield-dependencies provide. |
| 9 | B | Easy | Security | OAuth2PasswordBearer only extracts the token (and rejects a missing header); verification is the decode dependency's job. |
| 10 | D | Medium | Security | In FastAPI, per-route authentication is just a dependency: `Depends(get_current_user)` runs before the endpoint, and the 401 it raises blocks the handler entirely, so no endpoint logic runs with an invalid token. |
| 11 | A | Intense | Security | A signed JWT is self-contained: the signature proves authenticity, so no lookup is needed to trust the claims. |
| 12 | D | Medium | Middleware | Pre-endpoint rejection means a throttled request never triggers the paid LLM call. |
| 13 | C | Medium | SSE | The blank line is the SSE-specified delimiter between events. |
| 14 | D | Medium | WebSockets | SSE is the HTTP-native, one-way server-to-client stream built for read-only push and the browser reconnects automatically; a full-duplex WebSocket adds protocol overhead a client that never sends does not need. |
| 15 | C | Intense | WebSockets | WebSockets are full-duplex over one connection; SSE is server-to-client only. |
| 16 | B | Easy | Background | The client gets a job ID immediately; the work runs after the response is sent. |
| 17 | B | Medium | Testing | dependency_overrides swaps the dependency by function object with no endpoint changes. |
| 18 | D | Intense | Testing | Overrides live in the app's `dependency_overrides` dictionary and are never auto-cleared, so a stale fake keeps replacing the real dependency in later tests and can mask production behavior; suites must clear or re-override per test. |
| 19 | C | Medium | Routing | Construction-time dependencies are baked into the router and follow it to every mount. |
| 20 | B | Intense | Architecture | Middleware scopes to all routes; lifespan loads heavy resources once; `app.state` shares them with requests. |
