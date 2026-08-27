# Assignment: Dependency Injection for AI Session Management

This assignment contains 6 exercises designed to test your understanding of FastAPI's `Depends()` — what it does, how dependency chaining works, and what yield-dependencies guarantee. Complete these exercises without re-running the lab notebook.

---

## Exercises

### Exercise 1: Concept
In `get_session`, what does the `try: yield history / finally:` structure guarantee about when the `finally` block runs, relative to `chat()`?

### Exercise 2: Concept
If `get_session_id` raised an `HTTPException` before returning, would `get_session` or `chat()` ever run? Why or why not?

### Exercise 3: Concept
What happens to the `client` parameter in `chat()` if you remove `Depends(get_client)` from its type annotation and just declare it as `client: AsyncOpenAI`?

### Exercise 4: Code
Write a new dependency `get_message_count` that depends on `get_session` and returns only the count of user messages (not assistant replies). Inject it into `chat()` and include it in the response.

### Exercise 5: Code
Write a dependency `get_last_user_message(history: list = Depends(get_session))` that returns the content of the most recent user message in the history, or `None` if the history is empty.

### Exercise 6: Applied
If you called `/chat` three times on the same session, what would `turn_count` (from the Optional Exercise) be after the third call? Explain what value `len(history)` would have at that point and why.

---

## Answer Key & Explanations

### Exercise 1 Answer
- **Answer**: The `finally` block runs **after** `chat()` finishes, regardless of whether `chat()` succeeded or raised an exception.
- **Explanation**: In Python, a `finally` block always executes — after a `try` block completes normally, after a `return`, or after an exception propagates. In a yield-dependency, the code after `yield` runs after the endpoint finishes. So `get_session`'s `finally` block executes whether `chat()` returned a response or raised a `ValueError`.

### Exercise 2 Answer
- **Answer**: Neither `get_session` nor `chat()` would run.
- **Explanation**: FastAPI resolves the dependency chain in order: `get_session_id` → `get_session` → `chat()`. If `get_session_id` raises an exception, FastAPI stops resolving and returns an error response. `get_session` never gets called because its dependency failed, and `chat()` never gets called because its dependency (`get_session`) was never resolved.

### Exercise 3 Answer
- **Answer**: FastAPI would raise an error at startup (or at request time, depending on the version) because it can't resolve a parameter without `Depends()`. The endpoint would not function.
- **Explanation**: `Depends()` tells FastAPI to resolve the parameter by calling the specified function. Without it, FastAPI tries to treat the parameter as a query parameter, body parameter, or path parameter — but `AsyncOpenAI` isn't a valid request parameter type. The endpoint would fail to resolve the dependency.

### Exercise 4 Answer
- **Code**:
  ```python
  async def get_message_count(history: list = Depends(get_session)):
      """Returns count of user messages only."""
      return len([msg for msg in history if msg["role"] == "user"])
  ```
- **Injected into chat()**:
  ```python
  @app.post("/chat")
  async def chat(
      message: str,
      history: Annotated[list, Depends(get_session)],
      client: Annotated[AsyncOpenAI, Depends(get_client)],
      message_count: Annotated[int, Depends(get_message_count)],
      simulate_error: bool = False
  ):
      # ... existing code ...
      return {
          "answer": answer,
          "history": history,
          "message_count": message_count
      }
  ```
- **Explanation**: `get_message_count` depends on `get_session`, so FastAPI resolves the full chain: `get_session_id` → `get_session` → `get_message_count`. The list comprehension filters for `"role": "user"` to count only user messages.

### Exercise 5 Answer
- **Code**:
  ```python
  async def get_last_user_message(history: list = Depends(get_session)):
      """Returns the content of the most recent user message, or None."""
      for msg in reversed(history):
          if msg["role"] == "user":
              return msg["content"]
      return None
  ```
- **Explanation**: Iterating in reverse through the history finds the most recent user message. If the history is empty or contains no user messages, it returns `None`. This depends on `get_session`, so FastAPI resolves the session history before calling this function.

### Exercise 6 Answer
- **Answer**: `turn_count` would be `6` after the third call.
- **Explanation**: Each `/chat` call appends two messages to history: one user message and one assistant reply. After three calls: call 1 adds 2 messages (total: 2), call 2 adds 2 more (total: 4), call 3 adds 2 more (total: 6). `len(history)` returns 6 because it counts all messages (both user and assistant). The `turn_count` in the response would be `6` at the end of the third call.
