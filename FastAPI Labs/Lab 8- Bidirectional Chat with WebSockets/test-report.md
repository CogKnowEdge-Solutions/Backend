# Lab 8 — Bidirectional Chat with WebSockets — Test Report

Lab: lab-websockets-bidirectional-chat
Difficulty: Intermediate
Tester: [Agent]
Date: 2026-09-02

## Gate 1 (Fresh Environment): PASSED
Fresh venv created from scratch and Section 9's pip command executed exactly
(`fastapi==0.112.2 pydantic==2.8.2 httpx==0.28.1 python-dotenv==1.2.3 openai==3.5.0 uvicorn==0.30.6`).
All packages installed and imports verified. `.env` present with `OPEN_ROUTER_KEY`.

## Gate 2 (Clean Run): PASSED
- The sanity check was removed from the notebook (by request) and replaced with a
  dedicated Step 6 cell that defines `test_client = TestClient(app)` once, reused by
  all four demos.
- The monolithic `websocket_chat` handler was decomposed per request into four named
  functions, each in its own step: `generate()` (Cell 2), `handle_message()` (Cell 3),
  `handle_stop()` (Cell 4), and a lean `websocket_chat()` orchestrator (Cell 5).
- After the refactor, the protocol was revalidated deterministically with the standalone
  pytest suite (6/6 pass — see below) and against the real OpenRouter model:
  - Demo 1 (normal turn + history): second answer correctly referenced the first turn
    ("Your favorite color is teal."), proving history persisted across turns.
  - Demo 2 (queued message): after 2 tokens, a second message was acknowledged by a
    `queued` event immediately, generation finished with `done`, then the queued
    message was answered automatically as the next turn.
  - Demo 3 (stop): `Events after stop: ['cancelled']` with `'done' received: False` —
    no partial answer emitted or saved.
  - Demo 4 (disconnect): no unhandled error; context manager exited cleanly.

**Implementation note discovered during testing:** FastAPI's `@app.websocket`
handler parameter **must** be type-annotated with `WebSocket`
(`async def websocket_chat(websocket: WebSocket)`). Without the annotation FastAPI
does not recognize the argument as the WebSocket connection and the route rejects
the upgrade (the handler is never even called). This was found and fixed during the
original Gate 2 pass, and is explained in the lab's Step 5 markdown.

## Gate 3 (Output Verification): PASSED
Actual demo output matched Section 5's description. Section 5 was updated to show
Demo 1's two-answer output and Demo 3's `cancelled`/no-`done` result. The old
sanity-check example output was removed from Section 5 to stay consistent with the
notebook, which no longer contains the sanity check.

## Gate 4 (Optional Exercise): PASSED
Performed the Section 11 exercise: queued **3** messages during a single generation
(after 2 tokens). All three were acknowledged by `queued` events in order
(`Q one`, `Q two`, `Q three`), the initial generation finished normally, then all
three queued turns were processed one by one in FIFO order, each with its own `done`.
Order preserved as required.

## Gate 5 (Reviewer Walkthrough): PENDING
Requires a human reviewer. Hand off this report and the lab files for review.

## Supporting pytest run (protocol tests)
A standalone pytest file (`test_websockets_chat.py`) exercises the protocol
deterministically with a fake OpenRouter stream (no network). It mirrors the lab's
decomposed implementation exactly (`generate()`, `handle_message()`, `handle_stop()`,
and the `websocket_chat()` orchestrator). 6/6 tests passed after the refactor:

- `test_incremental_delivery` — status/token/done arrive incrementally
- `test_two_tokens_arrive_separately` — two tokens via separate receive calls
- `test_history_persists_across_turns` — two turns served on one connection
- `test_queued_message_is_acked_and_answered_later` — ack + later FIFO answer
- `test_stop_cancels_generation` — `cancelled` and no `done`
- `test_disconnect_cleanup` — clean exit, no unhandled error

Results recorded to `.xlsx` via `pytest_to_xlsx.py`:
`test-results/test_websockets_chat_2026-09-02.xlsx` (6 passed, 100% pass rate).

Overall: READY TO PUBLISH pending Gate 5 human review.
