# Lab 8 Assignment: Bidirectional Chat with WebSockets

Complete these hands-on tasks after finishing the lab. You will write the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through Cell 6 first so `app`, `test_client`, and the
`websocket_chat` handler all exist. After you edit the handler or its
helpers, re-run the edited cells before testing again. Each demo opens a
fresh connection, and each turn costs one (free-tier) LLM streaming call.

---

### Task 1 — Queuing a Wave of Messages

The lab's Demo 2 queues a single message during generation. Extend that to a
wave of three:

1. Open a fresh connection and send a message; wait for exactly 2 token
   events so generation has genuinely started.
2. Send **three** messages in rapid succession.
3. Watch the acknowledgments — then keep reading until all three queued
   turns have been answered.

- **Expected:** each of the three messages gets its own `queued`
  acknowledgment, in the order you sent them, *before* the current turn's
  `done` event. After that `done`, the queued turns are processed in order —
  each produces its own `status`/`token`/`done` sequence, and the third one
  completes last. The queue is a strict FIFO.

---

### Task 2 — The FIFO With No Popleft

The lab uses `collections.deque` for `pending_messages`, drained with
`popleft()`. Swap in the plain-list version:

1. Change the queue to a plain Python list, and use `pop(0)` where the code
   calls `popleft()`.
2. Re-run the Task 1 scenario (three messages queued during one
   generation).

- **Expected:** everything still works exactly the same — three `queued`
  acknowledgments in order, then all three turns answered in order. The
  `deque` is a performance choice (O(1) `popleft` vs O(n) `pop(0)`), not a
  correctness requirement — behavior is unchanged.

---

### Task 3 — Ping-Pong on the Same Channel

Add a third client-to-server message type, `{"type": "ping"}`, that the
server answers with `{"type": "pong"}` — without touching `history` or the
pending queue and without interrupting any in-flight generation. It needs
handling in **two** places:

1. **Idle case** — in the outer loop, before the `message` handling, for
   data that came from the fresh `websocket.receive_json()` wait.
2. **Mid-generation case** — in the race loop's result dispatch: a `ping`
   arriving through `recv_task` must be answered and a fresh `recv_task`
   created — it must **not** fall into the branch that queues messages
   (that branch would treat the ping as a chat turn and answer it later).

Test both:

- Open a connection and send `ping` before any message → **Expected:** an
  immediate `pong`.
- Send a message, wait for 2 tokens, then send `ping` → **Expected:** a
  `pong` arrives while generation keeps producing tokens, **no** `queued`
  acknowledgment, and the original answer still finishes with `done` (no
  spurious turn for the ping). The pong and the tokens may interleave in
  either order — check what appears, not the exact sequence.

---

### Task 4 — Waiting for Everything

The race uses `return_when=asyncio.FIRST_COMPLETED` so the server acts on
whichever of generation or the next client message finishes first. Replace
it with `return_when=asyncio.ALL_COMPLETED` and re-run **only** the Demo 3
scenario (send a message, wait for 2 tokens, then send `stop`):

- **Expected:** generation runs to completion and `done` arrives; you never
  see `cancelled`. The `stop` is received by the receive task but the wait
  does not return until the generation task finishes on its own, so the
  stop-handling branch is never reached — the client's request is silently
  ignored.

Two things to keep in mind while testing:

- The generation finishes naturally, so give it as long as a full answer
  takes — nothing is hung, that is the point.
- Do **not** test this change with the queued-message demo: under
  `ALL_COMPLETED` the wait blocks until generation ends, the `done` branch
  fires, and the client never receives the `queued` ack it is waiting for,
  so that demo would hang.