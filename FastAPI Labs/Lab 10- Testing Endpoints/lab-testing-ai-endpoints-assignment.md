# Lab 10 — Testing Endpoints with dependency_overrides — Assignment

**Complete these exercises from the lab alone. You do not need to re-run the notebook.**

---

### Exercise 1 — What `dependency_overrides` Actually Maps (Concept)

In the lab, `app.dependency_overrides[get_classifier_client] = lambda: fake_classifier` overrides the classifier dependency. The key used is the **function object** `get_classifier_client`, not the string `"get_classifier_client"`. What would happen if you accidentally wrote `app.dependency_overrides["get_classifier_client"]` instead (a string key)? Would the override take effect when the endpoint calls `Depends(get_classifier_client)`? Why or why not?

---

### Exercise 2 — Why `call_count` Is More Reliable Than Response Shape Alone (Concept)

In `test_unsafe_message_rejected_without_reply_call`, you could in principle verify the replier was not called by checking that `data["reply"]` does not exist in the response. The lab instead asserts `fake_replier.call_count == 0`. Why is the `call_count` assertion strictly more informative? Describe a hypothetical scenario where the response shape looks correct but the replier was actually called (and explain why `call_count` would catch that while a missing `"reply"` key would not).

---

### Exercise 3 — Clearing Overrides Between Tests (Concept + Applied)

What would happen if you removed the `app.dependency_overrides.clear()` call between `test_safe_message_gets_approved_and_replied` and `test_unsafe_message_rejected_without_reply_call`? Would test 2 still pass? Explain step by step what the override state would be at the start of test 2, and how that affects the endpoint's behavior.

---

### Exercise 4 — Adding a Fifth Test for Classification "unknown" (Applied)

Write a `def test_unknown_classification_rejected():` function that overrides the classifier to return the string `"unknown"` and asserts the response status is `"rejected"` with reason `"unrecognized classification"` and the replier's `call_count` is 0. Do you need to override `get_reply_client` as well, or can you omit that override? Explain why.

---

### Exercise 5 — What Happens Without the `try/except` in the Endpoint (Concept)

The endpoint wraps `classifier(req.message)` in a `try/except` that returns `{"status": "error", "detail": ...}`. If you removed this `try/except` block and `test_classifier_failure_returns_clean_error` ran, what would `response.status_code` be instead of 200? What would `response.json()` return? Why does the absence of error handling cause a fundamentally different failure mode than a structured error response?

---

## Answer Key

### Answer 1

The override would not take effect. `app.dependency_overrides` is a dictionary keyed on the **function object itself** — Python treats `get_classifier_client` (the function) and `"get_classifier_client"` (the string) as completely different dictionary keys. When FastAPI resolves `Depends(get_classifier_client)`, it looks up the function object in the overrides dict, finds nothing (because only a string was stored), and falls back to the real dependency function. The test would silently pass against the production implementation instead of the fake, giving a false sense of correctness.

### Answer 2

A `call_count` assertion proves the code path was actually taken, while a missing `"reply"` key only proves the final output shape. Consider a hypothetical bug where `replier(req.message)` is called but its return value is accidentally discarded (e.g., assigned to a local variable but not included in the response dict). The response would have no `"reply"` key — so a shape-based assertion would pass — but the replier was actually called and spent real money (or time) on an LLM call it should have skipped. `call_count == 0` catches this because it directly measures invocation, not output.

### Answer 3

Without `app.dependency_overrides.clear()`, test 2 would inherit both overrides from test 1: the classifier would still be overridden to return `"safe"` (from test 1's override) and the replier would be overridden to return `"Hello! How can I help you today?"` (from test 1's fake_replier). When test 2 sets its own classifier override to `"unsafe"`, that replaces the classifier override, but the replier override from test 1 persists if test 2 does not set its own replier override. However, in the lab's code, test 2 does set its own replier override, so both overrides get replaced. The test would technically still pass — but only because test 2 explicitly overrides both dependencies. The real danger is in tests that omit one override (like test 4, which only overrides the classifier) — without `clear()`, a stale replier override from an earlier test would be in effect, potentially masking bugs.

### Answer 4

You do **not** need to override `get_reply_client` for this test. The endpoint's branching logic rejects the message before it reaches the replier call when classification is not `"safe"` — so the replier dependency is never resolved, and its override is irrelevant. This is the same principle demonstrated in test 2: the replier override exists as a safety net (to prove `call_count == 0`), but the endpoint's logic guarantees the replier is never called regardless. The test function would look like:

```python
def test_unknown_classification_rejected():
    fake_replier = make_fake_replier(response="This should never appear")
    app.dependency_overrides[get_classifier_client] = lambda: make_fake_classifier(response="unknown")
    app.dependency_overrides[get_reply_client] = lambda: fake_replier

    response = test_client.post("/submit", json={"message": "Some message"})
    data = response.json()

    assert data["status"] == "rejected"
    assert data["reason"] == "unrecognized classification"
    assert fake_replier.call_count == 0
```

### Answer 5

Without the `try/except`, when `make_fake_classifier(raise_error=True)` raises `RuntimeError("Classifier service unavailable")`, the exception would propagate up through FastAPI's request handling and produce an **HTTP 500 Internal Server Error**. `response.status_code` would be `500`, and `response.json()` would return a FastAPI default error body (something like `{"detail": "Internal Server Error"}`) — not the structured `{"status": "error", "detail": "Classifier service unavailable"}` the endpoint is designed to return. The fundamental difference: a 500 error tells the client "the server broke," while the structured error tells the client "this specific upstream service failed, here is exactly what happened." The `try/except` converts an unpredictable crash into a predictable, documented failure mode that clients can handle programmatically.
