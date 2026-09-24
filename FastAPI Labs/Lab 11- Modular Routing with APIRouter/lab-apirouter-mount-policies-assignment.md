# Lab 11 Assignment: Modular Routing with APIRouter + include_router

Complete these hands-on tasks after finishing the lab. You will write all the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through Proof 5 first so the `router`, both mounts, and the
`test_client` all exist. After you edit a cell, re-run it before sending the
requests the task describes. Only Task 1 makes a real LLM call; every other
task is blocked (or fixed) at the routing layer before any model work, so
they cost nothing.

---

### Task 1 — A Third Tenant: The /beta Mount

The lab proves a router can behave differently under two mounts. Add a third,
independent one:

1. Write a dependency of your own, e.g. `length_gate(payload: MessageIn)`
   that raises `HTTPException(status_code=400, detail="too long")` when
   `len(payload.message) > 50`.
2. Mount the same `router` under prefix `/beta` with this dependency
   attached (`app.include_router(router, prefix="/beta",
   dependencies=[Depends(length_gate)])`), and re-run the cell.
3. POST `/beta/message` with a short message (well under 50 characters),
   then WITH a message over 50 characters.

- **Expected:** the short message returns **200** with a real LLM reply; the
  long message returns **400** with your detail, and the endpoint never
  runs — the same gate, but only on the `/beta` mount, independent of
  `/public` and `/internal`.

---

### Task 2 — A Second Gate for /premium

Add a mount that rejects everything, to show a mount-time dependency can
stop every request regardless of content:

1. Write `rate_limit_check` — a simple dependency that unconditionally
   raises `HTTPException(status_code=429, detail="rate limit exceeded")`.
2. Mount the router under prefix `/premium` with
   `dependencies=[Depends(rate_limit_check)]` and re-run the cell.
3. POST `/premium/message` with an ordinary message body.

- **Expected:** **429** with `{"detail": "rate limit exceeded"}`. The
  dependency raises before `send_message` is entered, so no LLM call
  happens and no reply is generated. This is the same mechanism as
  `moderation_gate` — just with an unconditional condition, which proves
  the enforcement lives entirely in the mount, not in the endpoint code.

---

### Task 3 — When the Dependency Loses Its Body

This lab deliberately declares `payload: MessageIn` in both `moderation_gate`
and `send_message`, which is what lets FastAPI parse the request body once
and hand both consumers the same `MessageIn` instance. Break that link:

1. Change `moderation_gate`'s parameter from `payload: MessageIn` to
   `payload: str` and re-run the cell.
2. POST `/public/message` with `{"message": "What is FastAPI?"}`.
3. Put the annotation back to `payload: MessageIn` and re-run the cell so
   the next task starts from the working lab.

- **Expected:** **422** with a validation error whose location is the
  missing **query** parameter `"payload"` — FastAPI no longer recognises
  the dependency's parameter as a body field, so it looks for a query
  string instead and the gate never even inspects the message. With the
  `MessageIn` annotation restored, `/public/message` again returns **200**
  for the safe message. The shared type annotation *is* the link between
  body and dependency.

---

### Task 4 — Moderation Baked Into the Router

The lab attaches `moderation_gate` at **mount time** so only `/public` is
gated. Move the gate to **construction time** to see the gate follow the
router everywhere:

1. Change the router to
   `router = APIRouter(dependencies=[Depends(api_router_level_dep),
   Depends(moderation_gate)])`.
2. Change the public mount to `app.include_router(router, prefix="/public")`
   — no `dependencies=` argument at all — and re-run both cells.
3. POST the unsafe message (`"this is unsafe content"`) to
   `/internal/message`.

- **Expected:** **400** with `{"detail": "blocked by moderation"}` — the
  same message that previously returned **200** on the internal mount is
  now rejected there too, because the gate lives in the router object and
  applies to every mount. Construction-time dependencies are universal and
  follow the router; mount-time dependencies are per-`include_router()`
  call. This contrast is the whole point of the lab — the lab deliberately
  used mount-time placement so the router has no default behaviour and each
  mount can set its own. Leave the construction-time version in place once
  you have confirmed the behaviour.