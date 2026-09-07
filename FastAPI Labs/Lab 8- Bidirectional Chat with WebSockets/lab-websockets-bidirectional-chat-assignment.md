# Lab 8 — Bidirectional Chat with WebSockets — Assignment

**Complete these exercises from the lab alone. You do not need to re-run the notebook.**

---

### Exercise 1 — Why `pending_messages` Uses a `deque` (Concept)

The handler uses `collections.deque` for `pending_messages` rather than a plain Python list. What specific property of `deque` makes it the right choice here, given that messages arrive unpredictably while generation is in progress? Describe the operation that `deque` performs in O(1) time that a list would perform in O(n).

---

### Exercise 2 — Tracing the Race Loop (Short Code)

After `asyncio.wait` returns with `done` containing the `recv_task` (meaning a client message arrived first), the code calls `recv_task.result()`. What happens if you call `recv_task.result()` on the `gen_task` instead? Write one sentence explaining the outcome.

---

### Exercise 3 — What Happens Without the `try/finally` (Concept)

The `generate()` coroutine wraps the `async for chunk in stream` loop in a `try/finally` that calls `await stream.close()`. If a `stop` message arrives and `gen_task.cancel()` is called, the `async for` loop is interrupted mid-iteration. Without the `try/finally`, what happens to the underlying HTTP connection to OpenRouter? Describe one concrete consequence.

---

### Exercise 4 — Adding a `ping` Message Type (Short Code)

Add a third client-to-server message type: `{"type": "ping"}`. When the server receives a `ping`, it should immediately respond with `{"type": "pong"}` without touching `history` or `pending_messages`, and should not interrupt any in-flight generation. Write the code for handling `ping` inside the outer loop, showing where it fits relative to the `if data["type"] == "message"` and the `gen_task` / `recv_task` logic.

---

### Exercise 5 — Why `asyncio.FIRST_COMPLETED` and Not `asyncio.ALL_COMPLETED` (Concept)

Suppose you replaced `return_when=asyncio.FIRST_COMPLETED` with `return_when=asyncio.ALL_COMPLETED`. Describe what the server would do when a `stop` message arrives while generation is still running. Would the generation task be cancelled immediately? Explain why or why not.

---

## Answer Key

### Answer 1

`deque` performs `popleft()` — removing and returning the leftmost element — in O(1) constant time. A Python list performing `pop(0)` must shift every remaining element one position to the left, which is O(n) in the length of the list. Since `pending_messages` could accumulate multiple messages and is drained from the front every time the outer loop iterates, using `deque` avoids repeated linear-time shifts.

### Answer 2

Calling `recv_task.result()` on `gen_task` would return the `None` value that `generate()` implicitly returns (it has no explicit `return` statement), which is meaningless in this context. More critically, if the generation task has *not* finished yet, calling `.result()` on it would raise an `InvalidStateError` — you can only call `.result()` on a task that is already done.

### Answer 3

Without `try/finally`, when `gen_task.cancel()` is raised, the `async for chunk in stream` loop is interrupted but the stream object itself is never closed. The underlying HTTP connection to OpenRouter remains open, holding a socket and associated resources until Python's garbage collector eventually cleans it up (or it times out). In a production server handling many concurrent WebSocket connections, leaked stream connections would accumulate and exhaust file descriptors or memory. The `finally` block guarantees the connection is released the moment the task is cancelled, regardless of how the interruption occurs.

### Answer 4

```python
if data["type"] == "message":
    # ... existing generation logic ...
elif data["type"] == "ping":
    await websocket.send_json({"type": "pong"})
```

The `ping` handler sits at the same level as the `message` handler in the outer `while True` loop, before any generation starts. This means it is only checked when the server is waiting for a fresh message (the queue is empty and `websocket.receive_json()` has returned). If a `ping` arrives *during* generation, it will be received by the `recv_task`, evaluated in the race loop, and — since it is neither `stop` nor `message` — would need to be handled there too. To make `ping` work mid-generation, you would add a third branch inside the race loop:

```python
elif result["type"] == "ping":
    await websocket.send_json({"type": "pong"})
    recv_task = asyncio.create_task(websocket.receive_json())
```

This sends the pong immediately without interrupting generation and creates a fresh receive task to continue listening.

### Answer 5

With `return_when=asyncio.ALL_COMPLETED`, the `await asyncio.wait(...)` call would not return until *both* the generation task and the receive task have finished. When a `stop` message arrives, the receive task completes — but the generation task is still running. The server would continue waiting for the generation task to finish naturally, completely ignoring the user's stop request until generation completes on its own. The `gen_task.cancel()` line would never be reached because the code that calls it (the `result["type"] == "stop"` branch) is only executed after `asyncio.wait` returns, which would be too late. `FIRST_COMPLETED` is essential because the server must be able to act on the *first* thing that happens — whether that is generation finishing or a client message arriving — without waiting for the other.
