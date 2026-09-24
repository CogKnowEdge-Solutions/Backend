# Lab 2 — Exception Handling In FastAPI

Difficulty: Beginner | ~35-40 min

---

## 1. Lab Title

Exception Handling In FastAPI

---

## 2. Problem Statement / Use Case Overview

When your AI backend calls an external LLM provider like OpenRouter, the call can fail in ways that traditional REST APIs never have to plan for. A model name gets deprecated. The API key expires. The model takes too long to respond. And most distinctively — the API call technically succeeds but the provider's safety filters silently block the content, returning nothing usable. A production AI backend needs to catch all four of these upstream failures and return structured error responses instead of raw crashes. This lab teaches you how to build that using custom exception classes and FastAPI's `@app.exception_handler()` decorators.

---

## 3. Input Data

The input to this lab is a single user message sent to a `/chat` endpoint as a query parameter. No file uploads, databases, or external datasets are involved. The data flows through the OpenRouter API and back:

- **message**: A text string sent to the OpenRouter model (e.g., `"What is the capital of France?"`).
- **Failure flags**: Boolean query parameters (`deprecated_model`, `timeout_error`, `bad_key`, `unsafe_content`) that each trigger a different upstream failure mode for demonstration purposes.

This lab calls the real OpenRouter API using a free-tier API key. Cost per full run-through is approximately $0.00 (free tier).

---

## 4. Processing

The pipeline runs through a single `POST /chat` endpoint with the following logic:

1. **Parse flags**: Read the boolean query parameters to decide which model name, timeout, and API key to use.
2. **Create a fresh AsyncOpenAI client**: A new `AsyncOpenAI` client is created per request to avoid event-loop binding issues when using `TestClient` in a notebook.
3. **Try the OpenRouter call**: Call `chat.completions.create` wrapped in `asyncio.wait_for` with either a normal (20s) or artificial (0.1s) timeout.
4. **Check for safety block**: If `unsafe_content=True`, directly raise `LLMSafetyError` (simulates a silent safety filter rejection).
5. **Return answer**: If the call succeeds and content is safe, return the model's answer.
6. **Catch upstream errors**: `APIStatusError` with status 400 → `BadModelError`; status 401 → `LLMAuthError`. `asyncio.TimeoutError` → `LLMTimeoutError`. Each custom exception is caught by its registered `@app.exception_handler()`, which returns a structured JSON error with the correct HTTP status code.

---

## 5. Output

The endpoint produces five distinct outputs depending on which flag is set:

1. **Success (no flags)**: HTTP `200 OK` with `{"answer": "Paris is the capital of France."}` (or similar real OpenRouter response).
2. **Bad model (`deprecated_model=True`)**: HTTP `404 Not Found` with `{"error": "Model Not found", "message": "Model name is not valid"}`.
3. **Timeout (`timeout_error=True`)**: HTTP `504 Gateway Timeout` with `{"error": "Request Timed Out", "message": "OpenRouter API timed out"}`.
4. **Unsafe content (`unsafe_content=True`)**: HTTP `502 Bad Gateway` with `{"error": "unsafe content", "message": "unusable content returned"}`.
5. **Bad key (`bad_key=True`)**: HTTP `401 Unauthorized` with `{"error": "authorization error", "message": "Unable to authenticate with OpenRouter API"}`.

---

## 6. Tech Stack

- `fastapi==0.112.2` — Web framework with built-in exception handling
- `pydantic==2.8.2` — Request/response validation (used by FastAPI internally)
- `httpx==0.28.1` — HTTP client (used by TestClient under the hood)
- `openai==3.5.0` — OpenAI-compatible client for OpenRouter
- `python-dotenv==1.2.3` — Loads API keys from `.env` files

---

## 7. Underlying Concepts

### Why AI Backends Need Special Exception Handling

Traditional REST APIs talk to databases or internal services where failures are well-understood: connection refused, timeout, 500. AI backends talk to external LLM providers where failures are **AI-specific**: a model name that was deprecated last week, a response that takes 30 seconds instead of 2, an expired API key — and most distinctively, a response where the API call technically succeeds (HTTP 200) but the provider's safety filters silently blocked the content, leaving you with nothing usable. Handling all four gracefully, with structured JSON error responses instead of raw crashes, is what separates a production AI backend from a demo.

### Custom Exception Classes

Each upstream failure gets its own exception class: `LLMAuthError`, `LLMSafetyError`, `LLMTimeoutError`, and `BadModelError`. These are plain Python exception subclasses with no special behavior — they exist so that FastAPI can catch each one **by type** and route it to the right handler. This is the same pattern you'd use for any domain-specific error taxonomy.

### `@app.exception_handler()` — Application-Level Exception Catching

FastAPI lets you register exception handlers directly on the app using the `@app.exception_handler(ExceptionType)` decorator. When any exception of that type is raised during a request — whether inside a `try/except` block or not — FastAPI intercepts it and calls your handler function, which returns a `JSONResponse` with the right status code and error body.

This is fundamentally different from a local `try/except`:
- A `try/except` only catches exceptions in the code **inside that block**.
- An `@app.exception_handler()` catches exceptions **anywhere during the request lifecycle** — including exceptions raised inside a `try/except` that don't match the local `except` clauses.

### The Critical Detail: LLMSafetyError Propagation

In the `/chat` endpoint, `LLMSafetyError` is raised **directly inside the `try` block** — but neither `except` clause catches it. That's fine. The `except APIStatusError` only catches API-level client errors, and `except asyncio.TimeoutError` only catches timeouts. `LLMSafetyError` doesn't match either, so it propagates upward — and FastAPI's application-level handler catches it.

This is the single best illustration of why `@app.exception_handler()` is a distinct mechanism, not just a wrapper around `try/except`. Four completely different failure origins (a bad model name, a slow call, a bad key, and a manually-raised safety flag with no underlying SDK exception at all — `LLMSafetyError` is raised directly, not returned by the API) all resolve through the same clean handler pattern.

### Failure Simulation Strategy

Each failure mode is triggered by a boolean query parameter on the same endpoint, rather than separate endpoints per failure. This mirrors production code, where one call site handles whatever comes back:

- `deprecated_model=True` → uses an invalid model name → real `APIStatusError` (status 400) from OpenRouter → `BadModelError`
- `timeout_error=True` → wraps the call in `asyncio.wait_for` with a 0.1s timeout → real `asyncio.TimeoutError` → `LLMTimeoutError`
- `bad_key=True` → creates a client with an invalid key → real `APIStatusError` (status 401) from OpenRouter → `LLMAuthError`
- `unsafe_content=True` → directly raises `LLMSafetyError()` with no SDK exception → simulates a safety block where the API succeeds but returns no usable content

All four are equally "real" as demonstrations — they trigger real exceptions from the SDK or raise real application-level exceptions, just engineered through deliberately bad input rather than left to chance.

### Full Exception Flow Diagram

Every failure mode ends up in the same place — a FastAPI exception handler registered by exception type — no matter where in the function it was raised. Here's the full path:

```mermaid
graph TD
    A["POST /chat<br/>message + failure flags"]
    B["Try: call OpenRouter API<br/>via asyncio.wait_for"]
    C{"Call succeeds?"}
    D["unsafe_content=True?"]
    E["Return real answer"]
    F["raise LLMSafetyError"]
    G["except APIStatusError<br/>check e.status_code"]
    H["except TimeoutError"]
    I["raise BadModelError<br/>404 (app response)"]
    J["raise LLMAuthError<br/>401"]
    K["raise LLMTimeoutError"]
    L["FastAPI app-level handlers<br/>catch exception by type"]
    M["Structured JSON error<br/>+ correct status code"]

    A --> B
    B --> C
    C -->|Yes| D
    D -->|No| E
    D -->|Yes| F
    C -->|"No: APIStatusError"| G
    C -->|"No: TimeoutError"| H
    G -->|"status 400"| I
    G -->|"status 401"| J
    H --> K
    F --> L
    I --> L
    J --> L
    K --> L
    L --> M

    style A fill:#e1f5ff
    style B fill:#fff9c4
    style E fill:#c8e6c9
    style F fill:#ffccbc
    style I fill:#ffccbc
    style J fill:#ffccbc
    style K fill:#ffccbc
    style L fill:#ffe0b2
    style M fill:#c8e6c9
```

Notice that `LLMSafetyError` is raised directly, without going through either `except` block — it doesn't need to, because FastAPI's `@app.exception_handler()` catches exceptions at the application level, not just inside a local `try/except`. That's what lets four completely different failure origins (a bad model name, a slow call, a bad key, and a manually-raised safety flag) all resolve to the same clean, structured error pattern.

---

## 8. Prerequisites

- A free OpenRouter API key
- Basic familiarity with Python exceptions (`try`/`except`)

---

## 9. Environment / Dependencies Setup

To run this lab locally, perform the following commands in your shell:

```bash
# Create a fresh virtual environment
python -m venv venv

# Activate the virtual environment (Windows)
.\venv\Scripts\activate

# Install the dependencies
pip install fastapi==0.112.2 pydantic==2.8.2 httpx==0.28.1 openai==3.5.0 python-dotenv==1.2.3
```

Create a `.env` file in your project root with your API key:

```
OPEN_ROUTER_KEY=your_openrouter_api_key_here
```

---

## 10. Step-wise Development Instructions

### Cell 1: Dependency Installation

Installs all required packages with pinned versions in a single command.

```python
!pip install fastapi==0.112.2 pydantic==2.8.2 httpx==0.28.1 openai==3.5.0 python-dotenv==1.2.3
```

### Cell 2: Imports and API Key Setup

Load the modules, read the API key from `.env`, and create the FastAPI app. A fresh `AsyncOpenAI` client is created inside the endpoint per request — this avoids event-loop binding issues when using `TestClient` in a notebook.

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.testclient import TestClient
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai import APIStatusError
import asyncio
import os

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

if not api_key:
    api_key = input("Open Router API key: ")

app = FastAPI()
```

### Cell 3: Custom Exception Classes

Four exception types, one per upstream failure mode. Each has a docstring explaining what real-world failure it represents.

```python
class LLMAuthError(Exception):
    """Raised when the OpenRouter API rejects the API key (invalid credentials)."""
    pass

class LLMSafetyError(Exception):
    """Raised when the response is technically successful but contains no usable content (safety block)."""
    pass

class LLMTimeoutError(Exception):
    """Raised when the OpenRouter API does not respond within the allowed time."""
    pass

class BadModelError(Exception):
    """Raised when the requested model name is invalid or has been deprecated."""
    pass
```


### Cell 4: Auth Error Handler

`@app.exception_handler(ExceptionType)` tells FastAPI: "whenever this exception type is raised anywhere in the request lifecycle, call this function and return its response instead of crashing." Each handler below maps one custom exception to a specific HTTP status code and error message.

Maps `LLMAuthError` to HTTP 401 Unauthorized. The API key was rejected by OpenRouter.

```python
@app.exception_handler(LLMAuthError)
async def auth_error_handler(request: Request, exc: LLMAuthError):
    return JSONResponse(
        status_code = status.HTTP_401_UNAUTHORIZED,
        content = {
            "error": "authorization error",
            "message": "Unable to authenticate with OpenRouter API"
        }
    )
```

### Cell 5: Timeout Handler

Maps `LLMTimeoutError` to HTTP 504 Gateway Timeout. The upstream LLM took too long.

```python
@app.exception_handler(LLMTimeoutError)
async def timeout_handler(request: Request, exc: LLMTimeoutError):
    return JSONResponse(
        status_code = status.HTTP_504_GATEWAY_TIMEOUT,
        content = {
            "error": "Request Timed Out",
            "message": "OpenRouter API timed out"
        }
    )
```

### Cell 6: Safety Error Handler

Maps `LLMSafetyError` to HTTP 502 Bad Gateway. The API call succeeded but the content is unusable.

```python
@app.exception_handler(LLMSafetyError)
async def safety_error(request: Request, exc: LLMSafetyError):
    return JSONResponse(
        status_code= status.HTTP_502_BAD_GATEWAY,
        content = {
            "error": "unsafe content",
            "message": "unusable content returned"
        }
    )
```

### Cell 7: Bad Model Handler

Maps `BadModelError` to HTTP 404 Not Found. The model name is invalid or deprecated.

```python
@app.exception_handler(BadModelError)
async def bad_model(request: Request, exc: BadModelError):
    return JSONResponse(
        status_code = status.HTTP_404_NOT_FOUND,
        content = {
            "error": "Model Not found",
            "message": "Model name is not valid"
        }
    )
```

### Cell 8: The `/chat` Endpoint

This single endpoint handles everything: a normal call, plus four ways it can fail upstream. Each boolean query parameter simulates a different failure:
- `deprecated_model=True` → invalid model name → `APIStatusError` status 400 → `BadModelError`
- `timeout_error=True` → artificially short timeout → `asyncio.TimeoutError` → `LLMTimeoutError`
- `bad_key=True` → invalid API key → `APIStatusError` status 401 → `LLMAuthError`
- `unsafe_content=True` → directly raises `LLMSafetyError` (no SDK exception — simulates a safety block where the API succeeds but returns nothing usable)

```python
@app.post("/chat")
async def chat(
    message: str, 
    deprecated_model: bool = False, 
    timeout_error: bool = False,
    bad_key: bool = False,
    unsafe_content: bool= False):
    try:

        # bad_key=True uses a deliberately invalid key to simulate an auth failure
        active_client = AsyncOpenAI(
            api_key="Invalid_API_Key",
            base_url="https://openrouter.ai/api/v1"
        ) if bad_key else AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Pick model name and timeout based on failure flags
        model_name = "invalid_model_name" if deprecated_model else "openrouter/free" 
        timeout = 0.1 if timeout_error else 20

        # Call OpenRouter with a hard timeout
        response = await asyncio.wait_for(
            active_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": message}],
            ),
        timeout= timeout
        )


    except APIStatusError as e:
        if e.status_code == 400:
            raise BadModelError()
        if e.status_code == 401:
            raise LLMAuthError()
        
        return JSONResponse(
            status_code=e.status_code,
            content={
                "details": e.message
        }
    ) #catches unhandled errors

    except asyncio.TimeoutError as e:
        raise LLMTimeoutError()
    
    # Simulate a safety block: raise directly (no SDK exception to catch)
    if unsafe_content:
        raise LLMSafetyError()

    return {"answer": response.choices[0].message.content}
```

### Cell 9: TestClient Instantiation

Creates a test client to send requests to the FastAPI app directly in the notebook, without running a live server.

```python
test_client = TestClient(app)
```

### Cell 10: Success Case

A normal call with no failure flags. Confirms the happy path works and that exception handlers don't interfere.

```python
question = "What is the capital of France?"
res = test_client.post(
    "/chat",
    params={"message": question}
)
print(res.status_code)
print(res.json())
```

### Cell 11: Deprecated Model

Triggers a real `APIStatusError` (status 400) from OpenRouter by passing an invalid model name.

```python
question = "hello"
res = test_client.post(
    "/chat",
    params={
        "message": question,
        "deprecated_model": True
    }
)

print(res.status_code)
print(res.json())
```

### Cell 12: Timeout

Triggers a real `asyncio.TimeoutError` by setting an artificially short timeout.

```python
question = "hello"
res = test_client.post(
    "/chat",
    params={
        "message": question,
        "timeout_error": True
    }
)

print(res.status_code)
print(res.json())
```

### Cell 13: Unsafe Content

Simulates a safety block by directly raising `LLMSafetyError` with no underlying SDK exception.

```python
question = "hello"
res = test_client.post(
    "/chat",
    params={
        "message": question,
        "unsafe_content": True
    }
)

print(res.status_code)
print(res.json())
```

### Cell 14: Bad Key

Creates a client with a deliberately invalid API key, triggering a real `APIStatusError` (status 401) from OpenRouter.

```python
question = "hello"
res = test_client.post(
    "/chat",
    params={
        "message": question,
        "bad_key": True
    }
)

print(res.status_code)
print(res.json())
```

---

## 11. Optional Exercise

Add a new custom exception, `LLMEmptyMessageError`, and a matching `@app.exception_handler()` that returns a `400 Bad Request` status code with a clear message. Raise it inside the `chat()` function at the very start — before any OpenRouter call — if `message` is an empty string. Test it with a `TestClient` call passing `message=''`.

---

## 12. What We Learnt

- How `@app.exception_handler()` catches exceptions at the application level, independent of local `try/except` blocks — as demonstrated by `LLMSafetyError` propagating without being caught locally
- Why one endpoint with one `try/except` can still cleanly handle several distinct upstream failure shapes by branching on exception type and error code
- The difference between a "loud" failure (a raised exception, like a timeout or bad key) and a "silent" failure (a technically successful response with no usable content, like a safety block)
- Why AI backends need exception handling that goes beyond what a typical REST API needs, since the upstream dependency is a non-deterministic model, not just a database or a simple service
