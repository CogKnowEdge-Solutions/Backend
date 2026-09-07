# Assignment: Modular Routing with APIRouter + include_router

This assignment contains 5 exercises designed to test your understanding of `APIRouter`, `include_router()`, mount-time vs. construction-time dependencies, and how the same router can serve different behaviour under different mounts. Complete these exercises without re-running the lab notebook.

---

## Exercises

### Exercise 1: Concept

The `moderation_gate` dependency accepts `payload: MessageIn` — the same Pydantic model as `send_message`. What happens to the dependency and the endpoint if `moderation_gate` declared a different parameter (e.g., `payload: str`) instead? Would the dependency still receive the parsed request body?

### Exercise 2: Code

Write a new dependency `rate_limit_check` that always raises `HTTPException(status_code=429, detail="rate limit exceeded")`. Then write one line of code that mounts the same `router` under prefix `/premium` with this dependency, so that every POST to `/premium/message` is rejected with a 429.

### Exercise 3: Concept

If you changed the router construction to `router = APIRouter(dependencies=[Depends(moderation_gate)])` and then called `app.include_router(router, prefix="/public")` **without** the `dependencies=` argument, what would happen to requests at `/public/message`? Would moderation still apply? Why or why not?

### Exercise 4: Applied

You have the following router and endpoint defined:

```python
router = APIRouter()

@router.get("/health")
async def health():
    return {"ok": True}
```

You mount it three times:

```python
app.include_router(router, prefix="/v1")
app.include_router(router, prefix="/v2")
app.include_router(router, prefix="/v3")
```

How many distinct route entries does `app.routes` contain for `/health`? Write a short loop (3 lines max) that counts and prints the total number of routes whose path ends with `/health`.

### Exercise 5: Concept

In Proof 3, the code uses `public_handler is internal_handler` (Python's `is` operator) rather than `public_handler == internal_handler`. Explain why using `==` would be a weaker proof of reuse — what scenario could `==` pass for while `is` would correctly reject?

---

## Answer Key & Explanations

### Exercise 1 Answer

- **Answer**: The dependency would **not** receive the parsed request body as a `MessageIn` instance. FastAPI matches dependency parameters by type annotation: because the endpoint declares `payload: MessageIn`, FastAPI parses the body into a `MessageIn` and provides it to any dependency that also declares `payload: MessageIn`. If `moderation_gate` declared `payload: str`, FastAPI would try to resolve `str` as a query or path parameter instead — it would receive a string, not the parsed body, and would not be able to access `payload.message` the way it does now.

- **Explanation**: This is the key reason the lab declares the same `MessageIn` type on both the dependency and the endpoint — FastAPI's body-parsing machinery recognises the shared type annotation and passes the same parsed object to both consumers. A different type annotation breaks that link.

### Exercise 2 Answer

- **Code**:
  ```python
  def rate_limit_check(payload: MessageIn):
      raise HTTPException(status_code=429, detail="rate limit exceeded")

  app.include_router(router, prefix="/premium", dependencies=[Depends(rate_limit_check)])
  ```
- **Explanation**: The dependency is mounted via the `dependencies=` argument on `include_router()`. Every POST to `/premium/message` will trigger `rate_limit_check` before the endpoint runs, and the 429 will be returned immediately. The endpoint is never entered.

### Exercise 3 Answer

- **Answer**: Yes, moderation would still apply to both `/public/message` and `/internal/message`. When dependencies are specified at `APIRouter()` construction time, they apply to every route on that router regardless of how it is later mounted. So even though the `include_router()` call has no `dependencies=` argument, the router-level `moderation_gate` is already attached to the `/message` and `/apirouter_dependency` routes and will run on every request to both mounts.

- **Explanation**: This is the core difference between the two placement points. Construction-time dependencies are universal — they follow the router wherever it goes. Mount-time dependencies are specific to one `include_router()` call. In this lab, mount-time placement is chosen deliberately so the router has no default behaviour and each mount can set its own.

### Exercise 4 Answer

- **Answer**: 3 distinct route entries. Each `include_router()` call registers a fresh copy of every route on the router under the given prefix.

- **Code**:
  ```python
  count = sum(1 for route in app.routes if getattr(route, "path", "").endswith("/health"))
  print(f"Health routes: {count}")
  ```

- **Explanation**: The router object is the same Python object in all three calls, but each `include_router()` call creates a new set of route entries on the app. There is one `/v1/health`, one `/v2/health`, and one `/v3/health` — three separate route entries, all backed by the same `health` function.

### Exercise 5 Answer

- **Answer**: `==` compares values — it checks whether two function objects are equal. In Python, two distinct function definitions with identical bodies and names would typically compare as not equal (functions are not value-equal by default), but if two functions happened to share metadata or if someone overrode `__eq__`, `==` could pass without the objects being the same. `is` checks identity: whether both names refer to the **exact same object in memory**, which is the only reliable way to confirm there is truly one function serving both mounts, not two separate definitions.

- **Explanation**: The point of Proof 3 is not just that the two endpoints behave the same, but that they are literally the same piece of code — one function object. `is` is the correct operator for identity checks; `==` is the correct operator for value equality, and is weaker for proving reuse.
