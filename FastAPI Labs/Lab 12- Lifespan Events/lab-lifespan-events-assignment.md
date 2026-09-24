# Lab 12 Assignment: Lifespan Events

Complete these hands-on tasks after finishing the lab. You will write the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through Proof 4 first so the `lifespan` function, the app,
both endpoints, and both `TestClient` patterns exist. After you edit a cell,
re-run it before testing. This lab makes no LLM calls — everything is
`time.sleep(5)`-based, fully deterministic, and adds roughly 10 seconds of
deliberate sleep to your run.

---

### Task 1 — A Second Resource Loaded Once

The lab loads one resource (the index) once, at startup. Add a second one to
prove the same lifespan pays for *everything* up front:

1. Extend the `lifespan` function so startup also stores a config dict —
   e.g. `app.state.config = {"model": "gpt-4", "temperature": 0.7}` — in the
   same section that currently sets `app.state.index`. In the shutdown
   section (after `yield`), set `app.state.config = None` alongside the
   index cleanup.
2. Write the dependency `get_config(request: Request)` that returns
   `request.app.state.config`, mirroring `get_index`.
3. Add a `GET /config` endpoint that returns the injected config dict.
4. Re-run the edited cells. Inside a fresh `with TestClient(app) as client:`
   block, GET `/config` and GET `/search?q=doc1` (the index proof for
   comparison). After the block closes, check `app.state.config`.

- **Expected:** `/config` returns the dict `{"model": "gpt-4",
  "temperature": 0.7}` instantly, and `/search` still works — the single
  startup `time.sleep(5)` loads *both* resources before the first request,
  so neither is reloaded per call. After the `with` block closes,
  `app.state.config is None`, exactly like the index: the shutdown half of
  the same lifespan cleaned up both resources.

---

### Task 2 — The State Nobody Loaded

The lifespan-backed app only has the index on `app.state` because the
lifespan function ran. `TestClient(app)` — plain instantiation — does
**not** run it; only entering `with TestClient(app) as client:` does.

1. Create a plain `client = TestClient(app)` (no `with` block, no requests
   inside anything) and GET `/search?q=doc1`.
2. Then run the same request inside `with TestClient(app) as client:`.
3. Print `response.status_code` (and `response.json()`) for both.

- **Expected:** the plain client returns **500** with the generic
  `{"detail": "Internal Server Error"}` — `lifespan` never started, so
  `app.state.index` was never assigned, and `get_index`'s
  `request.app.state.index` raised an `AttributeError` (the exception
  middleware turns it into the 500 rather than crashing the app). Inside
  the `with` block the same request returns **200** with the result. This
  is exactly why the lab's Proofs 2–4 wrap the client in the `with` block:
  entering it is what triggers startup (and exiting triggers shutdown).