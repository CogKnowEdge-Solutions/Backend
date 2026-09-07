# Assignment: Lifespan Events

This assignment contains 5 exercises designed to test your understanding of FastAPI lifespan events, `@asynccontextmanager`, `app.state`, and the distinction between dependency-scoped and app-scoped state. Complete these exercises without re-running the lab notebook.

---

## Exercises

### Exercise 1: Concept

In the lifespan function, what happens if you remove the `@asynccontextmanager` decorator and pass a plain async generator function to `FastAPI(lifespan=...)`? Would the code before `yield` still run at startup? Would you see any warnings?

### Exercise 2: Code

Write a lifespan function that loads a fake config dict `{"debug": True, "max_retries": 3}` into `app.state.config` at startup, and deletes `app.state.config` at shutdown. Include the decorator and the `yield`.

### Exercise 3: Concept

In Proof 1, the naive path uses `TestClient(app_naive)` (plain instantiation). In Proofs 2–4, the lifespan path uses `with TestClient(app) as client:` (context manager). Explain why Proof 1 deliberately avoids the `with` block, and what would happen if you accidentally used `with TestClient(app_naive) as client:` for the naive path.

### Exercise 4: Applied

A colleague writes this code, expecting it to work:

```python
from fastapi import FastAPI, Depends, Request

app = FastAPI()

def get_index(request: Request):
    return request.app.state.index

@app.get("/search")
def search(q: str, index=Depends(get_index)):
    return {"query": q, "result": index[q]}
```

They send a request to `/search?q=doc1` and get an error. What error is raised, and why does it happen? What is the missing piece that would fix it?

### Exercise 5: Code

Write a dependency `get_config(request: Request)` that reads `request.app.state.config` (assume it was populated by a lifespan function). Then write a `GET /config` endpoint that uses this dependency and returns the config dict as JSON.

---

## Answer Key & Explanations

### Exercise 1 Answer

- **Answer**: In the current version of Starlette (0.38.6), a plain async generator function without `@asynccontextmanager` still works — Starlette detects it and wraps it automatically. However, it emits a `DeprecationWarning` advising you to use `@asynccontextmanager` instead. The `@asynccontextmanager` decorator is still the correct approach because: (a) it avoids the deprecation warning, (b) it makes the intent explicit that this is a context manager with startup/shutdown halves, and (c) future versions of Starlette may remove the automatic wrapping entirely.

- **Explanation**: The `@asynccontextmanager` decorator converts the generator into an object that explicitly supports the async context manager protocol (`__aenter__` / `__aexit__`). Starlette enters the context manager at startup (running code before `yield`) and exits it at shutdown (running code after `yield`). While Starlette currently handles the case where the decorator is missing, this is deprecated behaviour — relying on it means your code may break when Starlette removes the automatic wrapping in a future version.

### Exercise 2 Answer

- **Code**:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      app.state.config = {"debug": True, "max_retries": 3}
      yield
      del app.state.config
  ```
- **Explanation**: The structure mirrors the lab's `load_index` pattern: code before `yield` runs at startup and populates `app.state`; code after `yield` runs at shutdown and cleans up. Using `del` instead of setting to `None` is a stylistic choice — both work. The key requirement is that the decorator is present and `yield` appears exactly once.

### Exercise 3 Answer

- **Answer**: Proof 1 avoids the `with` block because the naive path's endpoint never reads from `app.state` — it calls `load_index()` directly via its own dependency. Using plain `TestClient(app_naive)` is the minimal, fair way to exercise that endpoint without involving any lifespan machinery.

  If you used `with TestClient(app_naive) as client:` for the naive path, it would still work — the naive app has no lifespan function, so entering the `with` block would simply do nothing at startup and nothing at shutdown. The timing results would be identical. However, it would be misleading: it would look like you are testing lifespan behaviour when you are actually testing code that has nothing to do with lifespan.

- **Explanation**: The distinction matters for clarity of the proof, not for correctness. The naive path is intentionally tested without lifespan context to keep the comparison clean: plain instantiation triggers no lifespan events, so the only code that runs is the dependency calling `load_index()` on every request.

### Exercise 4 Answer

- **Answer**: The error is `AttributeError: 'State' object has no attribute 'index'`. Starlette initializes `app.state` as an empty `State` object. When `get_index` tries to read `request.app.state.index`, the attribute does not exist because no lifespan function has populated it. The fix is to add a lifespan function that loads the index into `app.state.index` before the app starts accepting requests:

  ```python
  from contextlib import asynccontextmanager

  def load_index():
      return {"doc1": "...", "doc2": "..."}

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      app.state.index = load_index()
      yield
      app.state.index = None

  app = FastAPI(lifespan=lifespan)
  ```

- **Explanation**: This is exactly why lifespan events exist in this lab's design — the dependency reads from `app.state`, but something must populate `app.state` before any request arrives. Without a lifespan function, the attribute is never set, and the first request that tries to read it gets an `AttributeError`. The lifespan function ensures the attribute is populated exactly once at startup.

### Exercise 5 Answer

- **Code**:
  ```python
  def get_config(request: Request):
      return request.app.state.config

  @app.get("/config")
  def read_config(config=Depends(get_config)):
      return config
  ```
- **Explanation**: The dependency follows the same pattern as `get_index` in the lab — it receives a `Request` object, accesses `request.app.state`, and returns the stored value. The endpoint uses `Depends(get_config)` to receive the config dict as its `config` parameter. This works because the lifespan function (not shown here) must have already populated `app.state.config` before any request is accepted — otherwise `request.app.state.config` would raise an `AttributeError`.

---

## Attempt Verification

Try each exercise in a scratch Python file or notebook before checking the answer key. For Exercises 2 and 5, verify the code runs without errors. For Exercises 1, 3, and 4, reason through the answer before reading the explanation — the goal is understanding, not memorisation.
