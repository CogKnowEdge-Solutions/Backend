# Assignment: Exception Handling for Upstream LLM Failures

This assignment contains 6 exercises designed to test your understanding of application-level exception handling, custom exception classes, and how FastAPI routes errors from upstream LLM failures. Complete these exercises without re-running the lab notebook.

---

## Exercises

### Exercise 1: Concept
In the `/chat` endpoint, `LLMSafetyError` is raised directly inside the `try` block — but neither `except errors.ClientError` nor `except asyncio.TimeoutError` catches it. Why does the exception still get handled correctly, producing a clean `502 Bad Gateway` response instead of crashing?

### Exercise 2: Concept
What is the difference between a failure the Gemini SDK raises as an exception (like `ClientError`) and a failure you have to detect and raise yourself (like the safety block)? Why can't you always rely on the SDK to throw an exception?

### Exercise 3: Code
Write a new `@app.exception_handler()` for a hypothetical `LLMQuotaExceededError` exception that returns a `429 Too Many Requests` status code with the JSON body `{"error": "quota exceeded", "message": "Daily API quota exhausted"}`. Include both the exception class and the handler.

### Exercise 4: Code
The endpoint currently uses a local `try/except` to catch `errors.ClientError` and branch on `e.code`. Write an alternative approach that instead registers a separate `@app.exception_handler(errors.ClientError)` on the app and handles the code branching inside that handler. What advantage does this have over the current approach?

### Exercise 5: Concept
What happens if an exception is raised in `chat()` that doesn't match any of the four registered handlers (for example, a plain ValueError)? Does FastAPI still return a clean JSON error, or something else?

### Exercise 6: Applied
Extend the optional exercise from Section 11: after adding `LLMEmptyMessageError` for empty messages, also add an `LLMTooLongMessageError` that raises when `message` exceeds 500 characters, returning a `413 Payload Too Large` status code. Test it by sending a message that is 501 characters long.

---

## Answer Key & Explanations

### Exercise 1 Answer
*   **Explanation**: `LLMSafetyError` is not caught by the local `except` clauses because it doesn't match `errors.ClientError` or `asyncio.TimeoutError`. Since no local handler matches, the exception propagates out of the function and up through FastAPI's request lifecycle. FastAPI then checks its registered `@app.exception_handler()` decorators, finds the one registered for `LLMSafetyError`, and calls it. This is the key distinction: local `try/except` handles exceptions within a code block, while `@app.exception_handler()` handles exceptions anywhere during the request, even if they escape the local scope.

### Exercise 2 Answer
*   **Explanation**: The Gemini SDK raises exceptions like `ClientError` when something goes wrong at the HTTP/API level (bad request, auth failure, server error). These are "loud" failures — the SDK explicitly tells you something went wrong. A safety block is a "silent" failure: the API call succeeds with HTTP 200, but the response contains no usable content (or `response.candidates` is empty due to a safety filter). The SDK doesn't raise an exception for this — your application code has to detect it (e.g., by checking `response.candidates[0].finish_reason == "SAFETY"`) and raise the appropriate exception yourself. This is why AI backends need application-level exception handling that goes beyond what the SDK provides.

### Exercise 3 Answer
*   **Code**:
    ```python
    class LLMQuotaExceededError(Exception):
        """Raised when the daily API quota has been exhausted."""
        pass

    @app.exception_handler(LLMQuotaExceededError)
    async def quota_exceeded_handler(request: Request, exc: LLMQuotaExceededError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "quota exceeded",
                "message": "Daily API quota exhausted"
            }
        )
    ```
*   **Explanation**: The pattern is identical to the four handlers in the lab: define the exception class, register a handler with `@app.exception_handler()`, return a `JSONResponse` with the appropriate status code and error body. The `429` status code is the standard HTTP code for rate limiting.

### Exercise 4 Answer
*   **Code**:
    ```python
    @app.exception_handler(errors.ClientError)
    async def client_error_handler(request: Request, exc: errors.ClientError):
        if exc.code == 404:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "Model Not found", "message": "Model name is not valid"}
            )
        if exc.code == 400:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "authorization error", "message": "Unable to authenticate with Gemini API"}
            )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": "upstream error", "message": f"Gemini error: {exc.code}"}
        )
    ```
*   **Explanation**: This moves the error branching out of the `try/except` in `chat()` and into a dedicated application-level handler. The advantage is separation of concerns: the endpoint focuses purely on business logic (calling the LLM), while error classification lives in one centralized handler. It also means the same `ClientError` handling applies to any future endpoint that calls Gemini, not just `/chat`.

### Exercise 5 Answer
*   **Explanation**: If an exception has no matching @app.exception_handler(), FastAPI does not produce a clean JSON response — it returns a raw 500 Internal Server Error instead. This is exactly what the lab's four handlers are built to prevent for the failures they know about. It also shows why exception handlers are matched by type: only exceptions that match a registered class get the clean, structured treatment.

### Exercise 6 Answer
*   **Code**:
    ```python
    class LLMTooLongMessageError(Exception):
        """Raised when the user message exceeds the maximum allowed length."""
        pass

    @app.exception_handler(LLMTooLongMessageError)
    async def too_long_handler(request: Request, exc: LLMTooLongMessageError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "message too long", "message": "Message exceeds 500 character limit"}
        )
    ```
    Add at the start of `chat()`:
    ```python
    if len(message) > 500:
        raise LLMTooLongMessageError()
    ```
    Test:
    ```python
    long_message = "a" * 501
    res = test_client.post("/chat", params={"message": long_message})
    print(res.status_code)  # 413
    print(res.json())       # {"error": "message too long", "message": "Message exceeds 500 character limit"}
    ```
*   **Explanation**: This follows the exact same pattern as `LLMEmptyMessageError` from the optional exercise, but with a length check instead of an emptiness check. The `413` status code indicates the client sent a payload that is too large for the server to process. Both validations happen at the very start of `chat()`, before any Gemini API call is made, so invalid input is rejected cheaply.
