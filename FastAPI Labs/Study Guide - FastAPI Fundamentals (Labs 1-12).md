# Study Guide — FastAPI Fundamentals (Labs 1–12)

This study guide is a question-and-answer companion to the FastAPI lab series. It covers the **concepts and framework mechanics** the labs teach — not the design of the labs themselves. Work through it in order as a revision path, or jump to any section you want to consolidate.

Each entry gives you:
- the **question**, phrased the way an instructor would ask it,
- a **short answer** to anchor the idea,
- a plain-language **"let's unpack it"** explanation (with a small code snippet wherever the mechanism is clearer in code),
- and a bold **Key takeaway** to remember.

---

## 1. Pydantic Validation

### Q1. How does declaring a Pydantic `BaseModel` request-body type hint give you automatic validation?

**Short answer:** When you type a route parameter as a Pydantic model, FastAPI parses the incoming JSON body, validates it against that model, and hands your function a fully instantiated, validated object — rejecting bad input with a `422 Unprocessable Entity` before your code runs a single line.

**Let's unpack it.** Pydantic models are the contract for what a valid payload looks like:

```python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    messages: Message                 # a nested model
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: int = Field(gt=0)
```

When you write `def chat(request: ChatRequest):`, FastAPI uses the type hint itself as the plan: it reads the body, decodes it as JSON, runs it through Pydantic, and either gives you a ready-to-use `ChatRequest` object or returns a structured 422 listing exactly which field failed (`temperature must be less than or equal to 1.0`, `field required`, and so on). You never write a single `if` statement for validation.

The same type hints do double duty: FastAPI generates the interactive Swagger docs at `/docs` straight from them — your schema *is* the documentation.

**Key takeaway:** In FastAPI, "type hint `BaseModel`" = automatic request parsing + validation + a 422 on failure + free API docs.

---

### Q2. How does Pydantic *enforce* constraints and *coerce* types?

**Short answer:** Pydantic enforces rules you declare with **type hints**, **`Field` constraints**, and **`Literal`** — and it actively tries to *coerce* values to the declared type before rejecting them.

**Let's unpack it.** There are three layers at work:

- **Type hints.** Declaring `content: str` means Pydantic checks (and, where safe, converts) the incoming value to a string.
- **`Field` constraints.** You add numeric or length bounds: `min_length=1` for non-empty strings, `ge=0.0` (greater-than-or-equal) and `le=1.0` (less-than-or-equal) for bounded floats, `gt=0` for strictly positive integers. Any value outside the bound fails validation.
- **`Literal[...]`.** This restricts a field to a fixed set of allowed strings, e.g. `role: Literal["user", "assistant"]`. Anything else is rejected by the type system itself.

The word *coercion* is important. Pydantic doesn't just check types — it converts when the conversion is unambiguous. If a field is declared as `int`, the string `"42"` and the float `42.0` both become the integer `42`. Only when a value truly can't be converted (like `"forty-two"`) does it raise a `ValidationError`, which reports *which* field failed, *where* it lives, and *why*.

**Key takeaway:** Pydantic = type hints (structure) + `Field` bounds and `Literal` (rules) + coercion (leniency) — and when none of those hold, a detailed, structured error instead of a crash.

---

## 2. Exception Handling

### Q3. What does `@app.exception_handler()` do, and how is application-level exception handling different from a local `try/except`?

**Short answer:** `@app.exception_handler(SomeType)` registers a handler that catches exceptions of that type *anywhere in the request lifecycle*, while `try/except` only catches exceptions inside the block it wraps.

**Let's unpack it.** A local `try/except` is literal and local: if you don't put the code inside the `try`, the `except` never sees it. An application-level handler is global:

```python
class BotDownError(Exception):
    pass

@app.exception_handler(BotDownError)
async def bot_down_handler(request, exc):
    return JSONResponse(status_code=503, content={"error": "bot unavailable"})
```

Now imagine code raises `BotDownError` in the middle of your route, inside a `try` block whose `except` clauses only handle, say, `KeyError` and `TimeoutError`. The local `except` clauses don't match, so the exception keeps propagating — and FastAPI's registered handler catches it at the application level and turns it into the response above. The handler receives the original `request` and the raised `exc`, so it can shape the error response however it needs.

**Key takeaway:** `try/except` is scoped to a code block; `@app.exception_handler()` is scoped to the whole request — even exceptions no local handler matches still get a clean, structured response.

---

### Q4. How do custom exception classes + one handler per type map distinct failures to specific HTTP status codes and structured JSON responses?

**Short answer:** Give each failure its own exception class, register one `@app.exception_handler(...)` per class, and let each handler return a `JSONResponse` with the status code and body that fit that failure. From any route, `raise` is enough — FastAPI routes the exception to the right handler for you.

**Let's unpack it.** Let's build the pattern from scratch with a concrete case: asking for an item that doesn't exist should produce a clean 404, not a Python traceback.

**Step 1 — the exception class.** One per failure kind. A plain subclass is all you need; its *type* is what routes it.

```python
class ItemNotFoundError(Exception):
    """Raised when a requested item does not exist."""
```

**Step 2 — the handler.** One handler per exception type. It receives the original `request` and the raised `exc`, and returns a structured response with the right status code.

```python
@app.exception_handler(ItemNotFoundError)
async def handle_item_not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "item_not_found", "message": "No item with that id."},
    )
```

**Step 3 — raise it, don't catch it.** The route has no `try/except` at all:

```python
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id != 42:
        raise ItemNotFoundError()
    return {"item": "the one item that actually exists"}
```

`GET /items/99` now answers with status `404` and body `{"error": "item_not_found", "message": "No item with that id."}` — a clean, structured error instead of a crash.

The pattern pays off when there are *several* failure kinds. You add a class and a handler per failure:

- `ItemNotFoundError` → 404 (not found)
- `OutOfQuotaError` → 429 (too many requests)
- `ProviderDownError` → 503 (service unavailable)

Each route just raises whichever class fits the moment — the mapping to status code and body lives entirely in the handlers, so every failure gets the same consistent JSON shape, and no route needs any error-handling code of its own.

**Key takeaway:** Exception type → handler → status code + body. Raise anywhere, FastAPI maps it app-wide, and each failure kind gets one clean structured response.

---

## 3. Dependency Injection

### Q5. What does `Depends()` inject, how is it resolved before the endpoint runs, and why should an injected object be *shared*?

**Short answer:** `Depends(function)` tells FastAPI to call `function`, take its return value, and pass it into the endpoint as a parameter — resolved *before* the endpoint body runs. When that function returns one shared object, every request reuses it instead of rebuilding it.

**Let's unpack it.**

```python
client = AsyncOpenAI(api_key=key, base_url="...")   # built once

async def get_client():
    return client

@app.post("/chat")
async def chat(message: str, client=Depends(get_client)):
    ...
```

Three things make `Depends()` more than "just call the function yourself":

- **FastAPI manages resolution.** The dependency runs before the endpoint, and its result arrives as a ready parameter.
- **It caches per request.** If two parameters both depend on the *same* dependency, FastAPI calls it once.
- **It chains.** A dependency can itself declare `Depends(other)`. FastAPI resolves the whole chain in order — the endpoint never needs to know the chain exists.

Sharing matters because of *what you inject*. An HTTP client object holds connection pools and authentication setup — expensive to create. Build it once at module level and inject the same instance every request, and no request ever re-pays that setup cost. Recreating it inside the dependency each time would throw the work away on every single call.

**Key takeaway:** `Depends()` turns "a function that produces a value" into an injectable parameter, resolved pre-endpoint and cached per request — ideal for sharing one expensive object.

---

### Q6. What is a *yield-dependency*, and what does the code after `yield` guarantee?

**Short answer:** A yield-dependency is a dependency function that uses `try: <setup> / yield <value> / finally: <teardown>`. FastAPI runs the setup, yields the value into the endpoint, then runs the teardown **after the request finishes — whether it succeeded or raised**.

**Let's unpack it.**

```python
async def get_session(session_id: str):
    history = session_store.setdefault(session_id, [])
    try:
        yield history          # the endpoint receives this 'history'
    finally:
        print("request finished.")   # runs after the endpoint returns OR raises
```

The `yield` splits the function into two halves. Everything above it is "before the endpoint"; everything below is "after the endpoint." The `finally` block is the guarantee: a request that crashes still triggers the teardown. That makes yield-dependencies the natural place to manage resources that must be released or committed regardless of outcome — closing a database connection, logging completion, releasing a lock.

Notice this is exactly the shape of a context manager, expressed as a dependency.

**Key takeaway:** A yield-dependency guarantees its `finally` teardown runs after every request — success or failure — making it FastAPI's idiomatic setup/teardown hook.

---

## 4. Async/Await & File Upload

### Q7. What is the difference between declaring an endpoint with `def` vs `async def` in FastAPI?

**Short answer:** `def` endpoints run in a **threadpool**; `async def` endpoints run **directly on the event loop**. Which one you choose decides how FastAPI executes your function, which changes how slow operations are handled.

**Let's unpack it.**

- **`def`** — FastAPI hands the function to a separate thread from a pool. The function can block on slow sync I/O without freezing the event loop, because each request gets its own thread. Fine for quick, CPU-ish or sync-blocking work.
- **`async def`** — FastAPI runs the function *on* the event loop. The function must cooperate: when it hits an `await`, it yields control so the event loop can work on other requests while the awaited I/O (network call, DB query) is in flight.

For endpoints that mostly **wait on external resources**, `async def` is right: it doesn't tie up a thread while idle, and it's the only way to get concurrency inside the endpoint (see Q8). For endpoints doing genuine CPU computation, a plain `def` is actually the better answer, because the work can't be `await`ed anyway.

**Key takeaway:** Threadpool vs event loop. Network-bound endpoints → `async def`; CPU-bound or sync code → `def`.

---

### Q8. Why does using `await` inside a for-loop stay sequential, and what does `asyncio.gather()` change?

**Short answer:** `await` pauses *this* function until the awaited call completes — so an `await` in a loop waits for each call before starting the next. `asyncio.gather()` starts all the calls at once, so they run concurrently and the total time approaches the slowest call instead of the sum.

**Let's unpack it.** Both snippets are inside an async endpoint and both use `await` — but the timing is radically different:

```python
# Sequential: one waits for the previous one
for chunk in chunks:
    e = await embed(chunk)          # ~0.5s per call, 8 calls = ~4s

# Concurrent: all launched together
embeddings = await asyncio.gather(*[embed(c) for c in chunks])   # ~1s total
```

In the sequential loop, each `await` hands control to the event loop but the *next iteration can't start until that one returns*. `asyncio.gather()` is different: it schedules every awaitable on the event loop *before* waiting for any of them. While call 1 is waiting on the network, call 2 starts, then call 3, and so on — all 8 are in flight simultaneously. The event loop doesn't speed up any single call; it just overlaps the waiting.

**Key takeaway:** `await` in a loop is technically async but sequential. Real concurrency for independent calls needs `asyncio.gather()`, and the win grows with the number of independent slow calls.

---

## 5. Security (OAuth2 + JWT)

### Q9. What does `OAuth2PasswordBearer` do — and just as importantly, what does it *not* do?

**Short answer:** `OAuth2PasswordBearer(tokenUrl="/token")` is a security *scheme*, not a verifier. It advertises to the `/docs` UI where a token comes from, extracts `Authorization: Bearer <token>` from incoming requests, and rejects a *missing* header with a 401. It does **not** verify the token's signature, expiry, or contents.

**Let's unpack it.** Three responsibilities, all plumbing:

1. **Advertisement** — tells interactive clients (like the Swagger UI) that protected routes take a bearer token obtainable from `/token`.
2. **Extraction** — pulls the raw token string out of the request header (e.g. `OAuth2PasswordBearer(tokenUrl="/token")`).
3. **Presence check** — a request with no header at all is short-circuited with a 401 *before* your code runs.

What it deliberately leaves out is the *verification*, the part that decides the token is genuine. That job belongs to the identity dependency in Q11, which calls `jwt.decode()`. Keeping extraction and verification separate is the design: the scheme handles the plumbing, and your dependency handles the trust decision.

**Key takeaway:** `OAuth2PasswordBearer` answers "is there a bearer token?" — never "is this token valid?" Verification is your dependency's job.

---

### Q10. What is a JWT made up of — and how does verification actually work?

**Short answer:** A JWT is `<header>.<payload>.<signature>`. The **payload** holds the readable claims (who the user is, which tenant, when it expires); the **signature** is a hash of header + payload computed with the server's secret. Verification proves the token came from the server and hasn't been changed — because only the holder of the secret can produce a valid signature.

**Let's unpack it.**

```python
payload = {"sub": "alice", "tenant_id": "tenant-a", "exp": time.time() + 1800}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
# token looks like:  <header>.<payload>.<signature>
```

Three dot-separated parts:

- **Header** — declares the signing algorithm, e.g. `{"alg": "HS256"}`.
- **Payload** — the claims themselves: `sub` (user), `tenant_id`, `exp` (expiry). It's only base64-encoded, **not** encrypted — anyone can decode and read it. Don't put secrets in a JWT; the payload is public.
- **Signature** — the trust-bearing part: a hash computed over header + payload plus the server's secret.

Verification works in four mechanical steps:

1. split the token into header, payload, signature;
2. recompute the signature from header + payload using the secret;
3. compare with the supplied signature — a mismatch means the token was altered by someone who doesn't know the secret, so it's rejected;
4. check `exp` against the current time — a token past its expiry is rejected.

`jwt.decode(token, JWT_SECRET, algorithms=["HS256"])` does exactly these steps in one call (see Q11). The practical consequence: a client **cannot** edit its claims (say, swap in another tenant's `tenant_id`) without breaking the signature, so whatever survives verification genuinely came from the server and wasn't altered.

**Key takeaway:** JWT = readable payload + cryptographic signature. The signature — not secrecy — is the trust: a verified token is untampered and unexpired, so its claims can be trusted.

---

### Q11. What does the token → identity dependency pattern look like, and why does **one** `except` handle every failure?

**Short answer:** A dependency extracts the bearer token with `OAuth2PasswordBearer`, runs `jwt.decode(...)` on it (see Q10), and returns the identity claim — e.g. `tenant_id` — from the *verified* payload. Catching the single parent exception type `PyJWTError` collapses every decode failure into one clean 401.

**Let's unpack it.** This is the "extract, then verify" pipeline in one dependency:

```python
async def get_current_tenant(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["tenant_id"]
```

Two mechanisms do the heavy lifting:

- **`OAuth2PasswordBearer` handles the plumbing (see Q9)** — it pulls `Authorization: Bearer <token>` out of the header and 401s a *missing* one before your code runs.
- **`jwt.decode()` owns the verification (see Q10)** — in one call it recomputes and checks the signature *and* validates `exp`. It raises `ExpiredSignatureError` for expired tokens, `DecodeError` for garbage, and a few more — and every one of those inherits from one parent, `PyJWTError`. Catching the parent maps **every** failure shape to the same single 401, with no branching on error kind.

Routes that need protection just declare the dependency and receive verified identity:

```python
@app.post("/chat")
async def chat(message: str, tenant_id: Annotated[str, Depends(get_current_tenant)]):
    return {"you_are": tenant_id, "message": message}
```

`tenant_id` here is *evidence*, not a claim: it came out of a token that passed signature and expiry checks, so the endpoint trusts only what the server sealed.

**Key takeaway:** Extraction (`OAuth2PasswordBearer`) and verification (`jwt.decode`) are separate steps. Verification owns signature + expiry; one parent exception turns every failure into one 401.

---

## 6. Middleware & Observability

### Q12. What is `@app.middleware("http")`, and how is its scope different from `Depends()`?

**Short answer:** Middleware is a function that wraps the **entire request/response cycle for every route** in the app. A dependency is scoped to one endpoint's resolution; middleware intercepts everything, whether or not the route ever mentions it.

**Let's unpack it.**

```python
@app.middleware("http")
async def logging_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)     # runs the rest of the pipeline
    print(f"{request.url.path} took {time.time() - start:.3f}s")
    return response
```

A middleware function takes the `Request` and a `call_next` coroutine. `call_next` represents "the rest of the app": downstream middleware, routing, dependency resolution, and finally the endpoint. Anything you write **before** `await call_next(request)` runs pre-endpoint; anything **after** runs post-response.

The scope contrast with `Depends()` is the key idea:

- A **dependency** runs only when a route declares it. Add a new route and forget the dependency, and the check silently doesn't apply.
- **Middleware** applies to every route automatically — new ones included — because it wraps the app, not the endpoints.

That makes middleware the right home for anything that must apply everywhere — logging, headers, guard rails, timing.

**Key takeaway:** `Depends()` = per-route, opt-in. Middleware = app-wide, every route, wrapped around `call_next` — code before it runs pre-endpoint, code after runs post-response.

---

### Q13. What is `call_next`, and what's the difference between forwarding to the endpoint and returning a response early without calling it?

**Short answer:** `await call_next(request)` hands the request to the rest of the pipeline (eventually the endpoint) and returns its response. If you return a response yourself **without** awaiting `call_next`, the pipeline stops — the endpoint never runs, and nothing downstream ever sees the request.

**Let's unpack it.** The pipeline order is: request arrives → middleware pre-code → routing + dependencies → endpoint → middleware post-code → client. Two middleware behaviors:

- **Forwarding** — `response = await call_next(request)` — goes *through* the endpoint, then you can inspect or modify the completed response afterward.
- **Short-circuiting** — returning a response like `JSONResponse(status_code=429, ...)` without `call_next` — answers the client immediately. Because `call_next` was never awaited, the route was never even looked up and the endpoint literally never executes.

That early return is the whole reason guard rails belong in middleware: any **expensive or irreversible work that lives in the endpoint** (an external API call, a billed request, a heavy computation) simply never happens for rejected requests. There's no need for the endpoint to check anything or opt into anything.

**Key takeaway:** Awaiting `call_next` means "run the endpoint, then I'll look at the result." Returning early without it means "the endpoint never runs" — which is exactly when you want to stop a request cheaply.

---

### Q14. How does an endpoint hand data to middleware (running *after* it) via `request.state`?

**Short answer:** `request.state` is a plain attribute bag on the request object. The endpoint writes to it (`request.state.usage = {...}`); middleware — which runs after the endpoint — reads it back with `getattr(request.state, ...)`. It's the standard channel for request-scoped data that has to cross from endpoint to middleware.

**Let's unpack it.** Middleware sees only the finished response object — never what the endpoint did inside. When the endpoint produces data worth logging (token counts, a job id, a metric), `request.state` is the bridge: the endpoint writes, the middleware reads.

```python
@app.post("/chat")
async def chat(message: str, request: Request):
    response = await client.chat.completions.create(...)
    request.state.usage = {   # endpoint: write
        "prompt_tokens": response.usage.prompt_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return {"answer": response.choices[0].message.content}

@app.middleware("http")
async def logging_middleware(request, call_next):
    response = await call_next(request)   # endpoint runs, response comes back
    usage = getattr(request.state, "usage", None)   # middleware: read
    if usage:
        print(f"{request.url.path} used {usage['total_tokens']} tokens")
    return response
```

Two details keep the pattern safe:

- **Read with a default.** `getattr(request.state, "usage", None)` treats "not set" as just another value. On requests the endpoint never reached (e.g. short-circuited by an early return — see Q13), the attribute simply doesn't exist — and that's fine.
- **It's request-scoped.** The same request object travels through the whole lifecycle, so what's stored is visible anywhere that sees the request — and nothing leaks across requests.

**Key takeaway:** `request.state` is request-scoped scratch space: the endpoint writes observability data, middleware reads it after the response, and `getattr(..., None)` keeps the read safe when nothing was written.

---

## 7. Streaming Responses with SSE

### Q15. What is `StreamingResponse`, and what does streaming improve — and what does it *not* improve?

**Short answer:** `StreamingResponse` takes an **async generator** instead of a finished value and sends each `yield`ed piece to the client as soon as it's produced. Streaming makes the *first* output arrive much sooner (perceived latency) — it does **not** make the total work finish faster.

**Let's unpack it.** A normal endpoint `return`s a completed value; FastAPI serializes the whole body before sending anything. `StreamingResponse` changes the delivery model:

```python
@app.post("/chat/stream")
async def chat_stream(msg: ChatMessage):
    return StreamingResponse(stream_tokens(msg.message), media_type="text/event-stream")
```

where `stream_tokens` is an async generator that `yield`s chunks one at a time. The HTTP connection stays open, and each chunk is flushed the moment it's produced.

The stream here is formatted as **SSE (Server-Sent Events)** — a real protocol, not an invented format. Every event is made of `event:` and `data:` lines terminated by a blank line:

```
event: token
data: The

event: token
data:  capital

event: done
data: [DONE]
```

The blank line between events isn't decoration — it's the delimiter both browser `EventSource` clients and server-side parsers rely on; `event: done` tells the client the full response has arrived.

The honest summary of the benefit: a blocking endpoint delivers nothing until the entire answer exists (a blank screen for the full generation time). Streaming delivers the first token within moments of generation starting. The machine produces the answer at roughly the same speed either way — what changes is *when the client sees something*.

**Key takeaway:** `StreamingResponse` + async generator = incremental delivery. It cuts perceived latency (time-to-first-token), not total generation time.

---

### Q16. Why can't you return an error status once a stream has started, and how do you signal a mid-stream failure?

**Short answer:** Once the first chunk goes out, the status line (the `200`) is already sent and can't be rewritten. So a mid-stream failure is communicated *inside* the stream: the generator yields an explicit error event, then stops, and the connection closes normally.

**Let's unpack it.** In a normal endpoint you'd raise an exception and FastAPI would swap the response for a `500` — but that only works *before* bytes go out. Streaming commits the status immediately, so that route is closed; the failure has to travel inside the stream itself:

```python
async def stream_tokens(msg: str, simulate_error: bool = False):
    stream = await client.chat.completions.create(..., stream=True)
    produced = 0
    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if not delta.content:
                continue
            if simulate_error and produced >= 2:
                yield "event: error\ndata: Stream interrupted\n\n"
                return                     # signal the failure inside the stream
            yield f"event: token\ndata: {delta.content}\n\n"
            produced += 1
    finally:
        await stream.close()               # upstream resource always released
    yield "event: done\ndata: [DONE]\n\n"
```

When the interruption flag fires, the generator emits chunks first, then an `event: error`, then ends — the client sees a partial answer plus an explicit error signal, and the connection ends cleanly instead of hanging mid-stream. The `finally` is the guarantee: whether the loop finishes, the error path returns, or the client hangs up and the generator is cancelled, the upstream `stream.close()` always runs.

**Key takeaway:** After streaming starts, status codes are immutable — signal failures *inside* the stream (an error event + clean end), and always release the upstream stream in a `finally`.

---

## 8. WebSockets

### Q17. How are WebSockets full-duplex, in a way that HTTP and SSE are not?

**Short answer:** A WebSocket is one persistent, **full-duplex** connection: after the upgrade handshake, both client and server can send data at any time, independently, over the same socket. HTTP is request/response (one direction, connection torn down), and SSE is one-way (server→client, over a still-open HTTP response).

**Let's unpack it.** HTTP's model is strict: the client sends, the server responds, and that exchange is over. SSE keeps the response open so the server can keep pushing — but the client still has no channel *on that same connection* to send anything back.

A WebSocket endpoint breaks both limits:

```python
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()          # complete the handshake; connection now open
    ...
```

The key moments: the client asks to `upgrade` the connection from HTTP to WebSocket; `accept()` completes that handshake; from then on, both sides hold an open channel and can write whenever — the server can stream tokens while the client simultaneously sends a "stop" or a new message. There's no waiting for the other side to finish, and no new connection per exchange.

This two-way simultaneity is what makes features like cancelling a long generation mid-stream possible — structurally impossible over HTTP or SSE.

**Key takeaway:** HTTP = one-shot request/response; SSE = long-lived but one-way; WebSockets = a persistent, full-duplex channel where both sides write at any time.

---

### Q18. Walk through the life of a WebSocket connection in FastAPI — from handshake to teardown.

**Short answer:** The connection begins as an HTTP request carrying an upgrade header; FastAPI routes it to the `@app.websocket` handler; the handler calls `accept()` to complete the handshake; then it enters a **send/receive loop** over the open socket until either side closes it — leading to a `WebSocketDisconnect` that the handler catches to clean up.

**Let's unpack it.** Four phases, in order:

1. **Upgrade.** A normal HTTP request asks to switch protocols (`Connection: Upgrade`, `Upgrade: websocket`). FastAPI recognizes this and dispatches to the matching WebSocket route.
2. **Accept.** `await websocket.accept()` completes the handshake. Before this line, the connection is still plain HTTP; after it, the socket is a live two-way channel.
3. **Send/receive loop.** The handler lives for the whole conversation — `await websocket.receive_json()` blocks waiting for the next client message, `await websocket.send_json(...)` pushes structured JSON events back. The loop does both as long as the connection lives.
4. **Teardown.** When the client disconnects (in any state — even mid-generation), reading or sending raises `WebSocketDisconnect`. Catching it lets you cancel in-flight work and release resources before the handler returns.

```python
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json(...)
    except WebSocketDisconnect:
        ...
```

Because the handler is one long-lived function call, everything you keep in local variables survives across every loop iteration and every turn of the conversation (see Q19).

**Key takeaway:** Upgrade → `accept()` → send/receive loop → `WebSocketDisconnect` cleanup. The handler is one persistent function that lives exactly as long as the socket.

---

### Q19. Why do plain local variables persist across turns in a WebSocket handler, and why is disconnect cleanup a required pattern?

**Short answer:** A WebSocket handler is a single long-lived function call that never returns until the connection closes — so ordinary local variables like `history` survive across every turn. And because a client can vanish at any instant, the handler must catch `WebSocketDisconnect` and cancel any in-flight work.

**Let's unpack it.** This is the opposite of an HTTP endpoint. In HTTP, each request is a fresh function invocation: local variables are recreated and destroyed per call, which is why conversation state had to live in an external store. In a WebSocket handler, the *same* stack frame lives for the entire conversation, so `history = []` and a pending-message queue declared at the top are still there for message #2, #3, and beyond — no external storage needed.

The flip side of a long-lived connection is that the client can disappear at any moment — including while the server is mid-stream, producing tokens. If the handler doesn't detect that, it keeps working into a void, wasting compute and holding the socket. The fix is built into the pattern:

```python
except WebSocketDisconnect:
    if gen_task and not gen_task.done():
        gen_task.cancel()
```

On disconnect, any in-flight generation task is cancelled and the handler exits cleanly. Treating "client vanished" as an ongoing possibility — not an accident — is what separates a robust long-lived endpoint from one that leaks resources.

**Key takeaway:** Long-lived handler + local variables = built-in per-conversation state with no external store; `WebSocketDisconnect` handling ensures no work is silently leaked into the void.

---

## 9. Background Tasks

### Q20. How do FastAPI's `BackgroundTasks` work mechanically — what does `add_task()` do, and when exactly do the queued functions run?

**Short answer:** `BackgroundTasks` is an injectable object; `background_tasks.add_task(func, *args)` queues `func` to run **after the response has been sent** — in the order added, within the same process — so the client gets its answer immediately while the work happens later.

**Let's unpack it.**

```python
@app.post("/tasks")
async def submit(req: BatchRequest, background_tasks: BackgroundTasks):
    job_id = generate_job_id()
    job_store[job_id] = {"status": "pending"}
    background_tasks.add_task(process_batch, job_id, req.reviews)   # queued, not run now
    return {"job_id": job_id, "status": "pending"}
```

Three mechanics are worth pinning down:

- **It's a dependency.** Declaring `background_tasks: BackgroundTasks` makes FastAPI build an empty queue for this request and inject it.
- **`add_task` only queues.** The function isn't invoked at `add_task` time — the endpoint returns first.
- **Execution timing is the framework's promise.** After FastAPI transmits the response, it runs the queued calls in FIFO order, in the same process. The work is invisible to the response that's already gone out, which is exactly why the client never waits on it.

Two honest caveats, both framework properties: tasks are **in-process** — if the server restarts mid-task, that work is lost — and there's no built-in persistence or retry. A natural pairing is to give the task a `job_id`, store progress in a shared dict, and let the client poll a status endpoint; critical work that can't tolerate loss belongs in a real task queue (e.g. Celery, RQ) instead.

**Key takeaway:** `add_task()` queues work that runs **after** the response is sent, in order, in-process. The client gets its answer first and checks on the work later — but the work isn't persisted or retried across restarts.

---

## 10. Testing Endpoints

### Q21. What is `app.dependency_overrides`, and why does `TestClient` let you test without a running server?

**Short answer:** `app.dependency_overrides` is a plain dict that maps a dependency *function* to a replacement implementation — so tests can swap a real slow/non-deterministic dependency for a deterministic fake with **zero changes to endpoint code**. `TestClient` runs your endpoints **in-process**, so there's no port, no socket, and no server process to manage.

**Let's unpack it.** The override is keyed on the function object itself:

```python
@app.post("/submit")
async def submit(req: MessageRequest, classifier=Depends(get_classifier_client), ...):
    ...

# In a test:
app.dependency_overrides[get_classifier_client] = lambda: fake_classifier
response = test_client.post("/submit", json={"message": "Hello"})
app.dependency_overrides.clear()     # remove every override
```

Three mechanics worth naming:

- **Keyed by function, not string.** FastAPI looks up the dependency by the actual Python function object, so when the endpoint declares `Depends(get_classifier_client)`, the override supplies the fake. The endpoint never branches, flags, or knows about tests.
- **`TestClient` is in-process.** It calls your endpoint code directly, in-process — you still write HTTPX-style `.post()`/`.json()`, but there's no TCP connection underneath. That makes tests fast, deterministic, and free of port conflicts; it's the same code a real server would run, minus the network.
- **Overrides apply app-wide.** Replacing one dependency function affects *every* place that function appears in the resolution chain (see Q22).

This matters most when dependencies are slow or non-deterministic — a real LLM call is slow, costs money, and can't be coaxed into producing a specific malformed edge case on demand. A fake, by contrast, can return exactly `"safe"`, `"unsafe"`, `"maybe"` — or raise — every branch, instantly, every time.

**Key takeaway:** `app.dependency_overrides` (a dict keyed by the dependency function) swaps real dependencies for fakes with no endpoint changes, and `TestClient` runs everything in-process — fast and deterministic tests for non-deterministic dependencies.

---

### Q22. How far does an override reach, and why must you call `clear()` between tests?

**Short answer:** One override replaces every occurrence of that dependency function **anywhere in the dependency graph** — nested dependencies included. Overrides persist on the app object until removed, so tests must call `app.dependency_overrides.clear()` or one test's fake silently leaks into the next.

**Let's unpack it.** Dependencies can chain: endpoint → dependency A → dependency B. An override on B is honored wherever B is resolved, no matter how deep in the chain — you don't touch A or the endpoint. That reach is powerful: it means a single override can stub out a shared resource used by many routes.

The leak is the flip side. `app.dependency_overrides` is a living dict on the app instance — it does *not* reset between requests, between tests, or at the end of a test function. If test 1 overrides the classifier to always return `"safe"` and forgets to clear it, test 2 quietly runs against test 1's fake — and passes or fails for the wrong reasons. `app.dependency_overrides.clear()` wipes every entry, restoring production behavior for the next test.

A related testing point: asserting on the fake's own behavior — like counting how many times it was called — can prove *which code path* ran, not just that the response "looked right."

**Key takeaway:** Overrides reach the full dependency graph but persist until removed — `clear()` between tests keeps each test honest and prevents fakes from leaking across.

---

## 11. Modular Routing with APIRouter

### Q23. What is `APIRouter`, and when does each `dependencies=` apply — at construction time vs mount time?

**Short answer:** `APIRouter()` is a route container: routes attached to it only join the app when mounted with `app.include_router(router)`. A `dependencies=` list at **router construction** follows the router to every mount; a `dependencies=` list at **mount time** applies only to that one mount.

**Let's unpack it.** The setup to keep straight is **one router, two mounts**:

```python
router = APIRouter(dependencies=[Depends(api_router_level_dep)])   # (A) construction time

@router.post("/message")
async def send_message(payload: MessageIn, ...):
    ...

app.include_router(router, prefix="/public",                       # (B) mount time
                   dependencies=[Depends(moderation_gate)])
app.include_router(router, prefix="/internal")                     # (C) plain mount
```

Which dependencies run for each route:

| Request to | Dependencies that run |
|---|---|
| `/public/message` | `api_router_level_dep` (construction) **and** `moderation_gate` (mount) |
| `/internal/message` | `api_router_level_dep` only (construction) |

Why the asymmetry? The construction-time dependency is baked into the router object at line (A), so it follows the router to **both** mounts. The mount-time dependency was attached at the `include_router()` call at (B), so it applies **only** there. That means the *same* `send_message` endpoint runs once with a moderation gate (public traffic) and once without it (trusted internal traffic) — with zero moderation logic inside the endpoint. Enforcement is configured where the router is mounted, not in the function.

One consequence to remember: a mount-time dependency that declares a body model forces a body on **every route in that mount**, not just the ones that declare it.

**Key takeaway:** `APIRouter` keeps endpoint definitions separate from deployment. Construction-time `dependencies=` follow the router to every mount; mount-time `dependencies=` apply to one mount only — and both can run on the same endpoint.

---

## 12. Lifespan Events

### Q24. What are lifespan events, what does `@asynccontextmanager` do, and how does `app.state` share startup resources with every request?

**Short answer:** The `lifespan` parameter accepts an async context manager: code **before `yield`** runs once at startup (before any request is accepted), code **after `yield`** runs once at shutdown. Resources built at startup live on `app.state`, so every request and dependency can read them instantly.

**Let's unpack it.**

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.index = load_index()   # startup — runs once, before any request
    yield                           # app begins accepting requests here
    app.state.index = None          # shutdown — runs once, after all requests

app = FastAPI(lifespan=lifespan)

def get_index(request: Request):
    return request.app.state.index   # every request reads the already-loaded resource
```

The pieces fit together like this:

- **`@asynccontextmanager`** turns a generator into an async context manager, which is the shape FastAPI's lifecycle handling expects: the `yield` marks the point where the app transitions from "starting" to "accepting requests."
- **`app.state`** is the bridge. Whatever the lifespan function stores there is reachable from any handler or dependency via `request.app.state...`. That's how "loaded once" becomes "instantly available on every request."

The cost contrast is the point. A per-request dependency that loads the index would run `load_index()` on *every* call — three requests pay the load three times. Lifespan pays it **once**, at startup, no matter how many requests follow; that's what makes it the right home for loading models, building retrieval indexes, and opening connection pools.

**Key takeaway:** Lifespan = exactly one startup + one shutdown. Build expensive resources once into `app.state` and read them on every request — vs a dependency, which re-pays the cost per call.

---

### Q25. Middleware, dependencies, and lifespan events all execute code before an endpoint — how do the three differ in when they run and how often?

**Short answer:** By scope and frequency. **Lifespan** runs once per app (startup + shutdown). **A dependency** runs once per request, resolved before the endpoint runs. **Middleware** runs for every request to every route, wrapping the entire pipeline.

**Let's unpack it with a comparison.**

| | Lifespan event | Dependency | Middleware |
|---|---|---|---|
| **Runs when?** | Once: startup + shutdown | Before the endpoint, per request | Before and after the endpoint, per request |
| **How often?** | Once per app lifetime | Once per request (cached within the request) | Once per request, every route |
| **Scope** | App-scoped | Endpoint/call-scoped | App-wide, automatic |
| **Shared state** | `app.state` | Inject return value | `request.state` |
| **Typical use** | Expensive one-time setup (models, pools, indexes) | Per-request values the endpoint needs | Cross-cutting concerns (logging, guard rails) |

A few concrete differentiators:

- **Lifespan is the only "setup" here.** It runs outside any request — it cannot read request data, and it's for things that should exist *before traffic starts* (loading an index, opening a connection pool) and be disposed of *after* traffic stops.
- **A dependency is opt-in and request-aware.** It only runs if a route declares it, and it can read the request's own data (query params, headers, body) to produce the value it injects.
- **Middleware is unconditional and wrapping.** It intercepts every request even a route never mentions it, and it sees the request *and* the finished response, which is why it's the natural home for logging and rate limiting.

If all three "do something before the endpoint runs," the question is *how often* and *at what level*: once for the whole app, once per request on demand, or every request to every route.

**Key takeaway:** Lifespan = once per app; dependency = once per request, only where declared; middleware = every request, every route. Choosing between them is choosing scope and frequency, not which one "catches" code earliest.

---

*End of study guide.*