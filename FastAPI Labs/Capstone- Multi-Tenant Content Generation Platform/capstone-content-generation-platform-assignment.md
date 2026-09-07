# Capstone Assignment — Multi-Tenant AI Content Generation Platform

**Difficulty: Capstone | Architecture-focused exercises**

These exercises test your understanding of how the system's pieces connect, not just the syntax of individual features. Attempt every exercise, then check your answers against the key at the end.

---

## Exercise 1: Dependency Placement

The `/content` router uses `Depends(get_current_tenant)` on its endpoint rather than via `dependencies=[Depends(get_current_tenant)]` at the router level. The `get_current_tenant` function declares `request: Request = None` **and** `websocket: WebSocket = None`, even though this platform's entire content surface is the single WebSocket.

**a)** Why don't router-level `dependencies=[...]` apply to WebSocket routes?
**b)** This platform only ever exercises the WebSocket branch. What is gained by declaring `request: Request = None` and `websocket: WebSocket = None`, instead of a single required `websocket: WebSocket`?

---

## Exercise 2: The Suggestions Deque and Its Two Checkpoints

The pipeline checks `suggestions[tenant_id]` at **two** deliberate checkpoints: once right after title generation (checkpoint 1, feeding the draft) and once right after the draft (checkpoint 2, feeding a review pass). The checkpoints sit on the two long `await` points in the pipeline — the title call and the draft call.

**a)** Where exactly do the two checkpoint windows open and close, and what happens to a suggestion that arrives inside each one?
**b)** Why is the second checkpoint necessary if the first one already pulled suggestions?

**Hint:** Think about what a tenant on a live WebSocket can do at any moment while the pipeline is mid-flight.

---

## Exercise 3: Why `asyncio.create_task` Instead of Awaiting the Pipeline

The WebSocket endpoint starts the pipeline with `asyncio.create_task(run_pipeline(...))` and replies `accepted` immediately. Consider what would happen if instead the handler simply `await`ed `run_pipeline(...)` inside the receive loop.

**a)** While the handler was awaiting the pipeline, what message could the receive loop not process, and which feature would break as a result?
**b)** The endpoint sends an `ack` event when a suggestion is queued. What does that `ack` prove to the client, and why is it a useful piece of protocol design?

---

## Exercise 4: Lifespan Justification

The lifespan function creates two resources: `app.state.llm_client` (the OpenAI client) and `app.state.tenant_preferences` (the preferences store). The preferences store includes an `await asyncio.sleep(2)` simulating a slow load.

**a)** Could the LLM client be created per-request instead of at startup? Would the system still work?
**b)** Why is the `asyncio.sleep(2)` important for demonstrating the value of lifespan — what would the argument against using lifespan be if both resources were lightweight?

---

## Exercise 5: Tenant Isolation

In Demo 7 both tenants stay connected at the same time. bob opens his own WebSocket while alice's is still open; bob's suggestion is acked on *his* socket and lands in *his* deque, then both tenants send `generate` at the same moment and each receives exactly its own 5-event stream.

**a)** Which state structures keep tenant data separate, and what role does the JWT play?
**b)** If `connection_registry` stored a single global WebSocket reference instead of a `dict[str, WebSocket]`, what would break?

---

## Exercise 6: Failure Handling

When `simulate_failure=True`, the pipeline raises an exception at the review step. The exception is caught inside `run_pipeline` and relayed to the socket as an `error` event.

**a)** If the `try/except` inside `run_pipeline` were removed, what would the tenant observe — and why? (Think about how the pipeline was started.)
**b)** If `push_to_tenant` did not have its own `try/except` and the tenant's WebSocket had closed, what would happen to the pipeline's own error handling?

---

## Answer Key

### Exercise 1: Dependency Placement

**a)** FastAPI's router-level `dependencies=[...]` resolves dependency parameters from the ASGI scope, and for WebSocket routes it does not inject `Request` or `WebSocket` into router-level dependencies — both come through as `None`, so any dependency that reads headers would fail. Endpoint-level `Depends(get_current_tenant)` works because FastAPI injects the correct scope object (the `WebSocket`) into the endpoint's own dependency parameters.

**b)** A single required `websocket: WebSocket` parameter would actually work for the current WebSocket route — but it would lock `get_current_tenant` to WebSocket forever: on an HTTP route FastAPI provides a `Request`, never a `WebSocket`, so the dependency could not be reused there. Declaring both with `None` defaults keeps the function transport-agnostic — FastAPI fills in whichever object the current route provides (here always the `WebSocket`) — and the identical dependency would already protect any HTTP route added later. The `Request` branch is dormant in this platform, not actively used.

### Exercise 2: The Suggestions Deque and Its Two Checkpoints

**a)** Window 1 opens when `run_pipeline` starts and closes at the first checkpoint, immediately after the title LLM call returns. A suggestion arriving inside window 1 is pulled at checkpoint 1 and folded directly into the draft prompt (which is asked to open with its phrase). Window 2 opens right after checkpoint 1 and closes at checkpoint 2, immediately after the draft LLM call returns. A suggestion arriving in window 2 is pulled at checkpoint 2 and gets a dedicated review pass that rewrites the draft.

**b)** The second checkpoint is necessary because **a tenant on a live WebSocket can send a suggestion at any moment** while the run is in progress. The receive loop appends suggestions to the deque as they arrive, without waiting on the pipeline. A suggestion that lands after checkpoint 1 — e.g. while the draft is being written — is picked up only by checkpoint 2 and fed into the review pass. Without it, such a suggestion would be silently consumed by nothing until the next generation run.

### Exercise 3: Why `asyncio.create_task` Instead of Awaiting the Pipeline

**a)** If the handler `await`ed `run_pipeline` directly, the receive loop would be suspended inside that await for the entire pipeline — titles, draft, review. While it was suspended, `receive_json` would not be called, so an incoming `suggestion` message would sit unprocessed until the pipeline finished. The two checkpoints would never find it. `asyncio.create_task` starts the pipeline as a separate coroutine on the same loop, so the receive loop keeps reading and dispatching messages the whole time — this concurrency is what makes mid-run steering possible.

**b)** The `ack` proves the suggestion was received by the server and queued in the tenant's deque *before* the pipeline finished — it is a deterministic confirmation in the demo's event ordering. As protocol design, an acknowledgment solves the "did my message ever arrive?" ambiguity: the client can confirm the agent's instruction is (or at least was, at send time) in the queue, instead of guessing from the final content.

### Exercise 4: Lifespan Justification

**a)** The LLM client *could* be created per-request. The system would still work. But creating it per-request means every request pays the cost of building a new connection pool, which is wasteful — the pool exists to be reused. Lifespan ensures the pool is built once and shared.

**b)** If both resources were lightweight (no `asyncio.sleep(2)`), the argument for lifespan would be weaker: "why bother with a context manager when creating the client is nearly instant?" The `sleep(2)` simulates a genuinely expensive one-time load (like loading an ML model or building a search index), making the case that lifespan is not just nice-to-have but **necessary** — you wouldn't want to pay that 2-second cost on every single request.

### Exercise 5: Tenant Isolation

**a)** Two structures keep tenant data separate: `connection_registry` (a `dict[str, WebSocket]` keyed by tenant_id, so `push_to_tenant("tenant-a", ...)` only touches alice's socket) and `suggestions` (a `dict[str, deque]` keyed by tenant_id). The JWT plays the identity role: the signed `tenant_id` claim is what the dependency extracts, and because it is signed, alice cannot forge a token carrying bob's tenant_id.

**b)** With a single global WebSocket reference, only the most recent tenant to connect would be registered. Every `push_to_tenant(...)` would target the last-connected tenant — bob's events would go to whoever connected last, and vice versa. Complete isolation failure.

### Exercise 6: Failure Handling

**a)** `run_pipeline` is started with `asyncio.create_task`, so there is no `await` that would receive its exception. Without the internal `try/except`, the `RuntimeError` would propagate out of `run_pipeline` into the task, terminate the pipeline mid-stream, and surface only as *asyncio*'s "Task exception was never retrieved" warning. The tenant would get **no** `error` event and no `done` event — just silence. The internal `try/except` is what converts that failure into a visible, clean `error` event.

**b)** If `push_to_tenant` lacked its own `try/except` and the socket had closed, the `await ws.send_json(...)` would raise — and if that happened while the pipeline was trying to report an error, the exception would be raised *inside* the pipeline's `except` block, aborting the report itself. The tenant would lose the very notification that was meant to reach them. `push_to_tenant`'s `try/except` makes a closed connection a non-event, so the pipeline's own error handling can always complete.