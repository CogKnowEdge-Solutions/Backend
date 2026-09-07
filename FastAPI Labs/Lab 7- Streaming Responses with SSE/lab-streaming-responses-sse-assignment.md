# Lab 7 — Streaming Responses with SSE — Assignment

**Complete these exercises from the lab alone. You do not need to re-run the notebook.**

---

### Exercise 1 — Parsing an SSE Stream (Concept)

Given the following raw SSE text that a client receives from `/chat/stream`, write down which lines are `event: token` events and what text each one carries. Then state what happens after the final `event: done` line.

```
event: token
data: The

event: token
data:  capital

event: token
data:  of

event: token
data:  France

event: token
data:  is

event: token
data:  Paris

event: done
data: [DONE]
```

---

### Exercise 2 — Why `if delta.content:` Is Necessary (Concept)

OpenRouter's streaming API occasionally sends chunks where `chunk.choices[0].delta.content` is `None` or an empty string — these are keep-alive comments or metadata chunks, not real text output. If the `stream_tokens` generator skipped the `if delta.content:` check and yielded these chunks as `event: token` data, what problem would the client experience? Describe one specific consequence.

---

### Exercise 3 — Adding a Word-Count Event (Short Code)

Modify the `stream_tokens` generator so that, right before the final `event: done\ndata: [DONE]\n\n`, it yields one additional SSE event: `event: wordcount\ndata: <total number of output chunks yielded>\n\n`. Write only the changed lines of the generator (not the entire function). What must change in the generator to track the count?

---

### Exercise 4 — Error Handling Location (Concept)

Suppose you moved the `simulate_error` logic out of the generator and into the endpoint itself, wrapping it in a `try/except` block — catching an exception from the generator and returning a JSON error response. Why would this approach fail once the stream has already started sending chunks? Describe exactly what the client would see.

---

### Exercise 5 — Why `stream()` Matters (Applied)

A developer replaces the `http_client.stream()` call in Demo 2 with `http_client.post()`, reasoning that both send the same request to the same server. They then measure `time.perf_counter()` before and after the call. Would the measured "time to first output" be smaller, larger, or the same as the original streaming measurement? Explain what `http_client.post()` does with the response body that `http_client.stream()` does not, and why this matters for timing.

---

## Answer Key

### Answer 1

The `event: token` events carry the following text:
- "The"
- " capital"
- " of"
- " France"
- " is"
- " Paris"

That is 6 token events, each yielding a single word (some with a leading space). After the `event: done` line with `data: [DONE]`, the generator has finished and the connection closes — no further events are sent.

### Answer 2

The client would receive `event: token` events with empty or `None` data values. If the client concatenates all token data to display the response, it would accumulate meaningless empty strings in the output — potentially inserting blank lines, extra spaces, or corrupted formatting into the displayed text. More seriously, some SSE parsers may raise an error or behave unpredictably when `data:` is empty, because the SSE specification expects `data:` to carry actual content for a `token` event.

### Answer 3

No new counter is needed — the generator already tracks the count with `event_count`, which increments once per yielded chunk inside `if delta.content:`. The only change is to yield the new event just before the `done` sentinel:

```python
    yield "event: wordcount\ndata: {event_count}\n\n"
    yield "event: done\ndata: [DONE]\n\n"
```

The key point is placement: the `wordcount` event must be yielded *after* the `async for` loop ends (so the count is final) but *before* `event: done` (so the `done` sentinel stays the last event the client receives, which is the contract a client relies on to close the stream).

### Answer 4

Once `StreamingResponse` starts streaming, the HTTP response headers — including a 200 status code — have already been sent to the client. A `try/except` around the endpoint that tries to return a different response (e.g., a JSON error body with a 400 or 500 status code) would fail because the response is already committed. The client would see the partial stream of chunks followed by either a hanging connection (if the exception is caught silently) or an HTTP error mid-stream (if the exception propagates), neither of which is a clean error signal. The only correct approach is to yield an error event *inside the generator* and end the generator, which closes the connection gracefully.

### Answer 5

The measured time would be **significantly larger** — in fact, it would be approximately equal to the full completion time, not the streaming first-output time. `http_client.post()` reads the entire response body into memory before returning, which means it waits for the complete stream to finish (every chunk plus the `done` event). Only then does the response become available. `http_client.stream()` yields the response incrementally, allowing `iter_lines()` to process each line as it arrives — which is the only way to capture the time at which the *first* output was received, not the time at which the *last* chunk finished. Using `post()` for the streaming measurement would produce a result indistinguishable from the blocking measurement, completely defeating the purpose of the comparison.