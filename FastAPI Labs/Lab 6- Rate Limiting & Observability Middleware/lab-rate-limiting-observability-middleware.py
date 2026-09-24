from fastapi import FastAPI, Depends, Header, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collections import deque
from typing import Annotated
import os, time, json

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

conversation_store = {}
app = FastAPI()

def get_tenant_id(x_tenant_id: str = Header(default="anonymous")):
    return x_tenant_id

async def get_session_history(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    session_id: str,
):
    key = (tenant_id, session_id)
    if key not in conversation_store:
        conversation_store[key] = []
    return conversation_store[key]

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

async def get_client():
    return client

@app.post("/chat")
async def chat(
    message: str,
    session_id: str,
    history: Annotated[list, Depends(get_session_history)],
    client_dep: Annotated[AsyncOpenAI, Depends(get_client)],
    request: Request,
):
    history.append({"role": "user", "content": message})

    response = await client_dep.chat.completions.create(
        model="openrouter/free",
        messages=history,
    )

    answer = response.choices[0].message.content
    history.append({"role": "assistant", "content": answer})

    # Pass usage data back to middleware via request.state
    if response.usage:
        request.state.usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

    return {"answer": answer, "history": history}

RATE_LIMIT_WINDOW = 45   # seconds
RATE_LIMIT_THRESHOLD = 3  # max requests per tenant in window

rate_limit_store = {}  # tenant_id -> deque of timestamps

def _log(response, tenant_id, request, start_time):
    latency_ms = round((time.time() - start_time) * 1000, 2)
    usage = getattr(request.state, "usage", None)
    log_line = {
        "tenant_id": tenant_id,
        "path": request.url.path,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
    }
    if usage:
        log_line["prompt_tokens"] = usage["prompt_tokens"]
        log_line["completion_tokens"] = usage["completion_tokens"]
        log_line["total_tokens"] = usage["total_tokens"]

    print(json.dumps(log_line))

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_time = time.time()
    tenant_id = None

    # Only rate-limit /chat — the only route that triggers LLM costs
    if request.url.path == "/chat":
        tenant_id = request.headers.get("x-tenant-id", "anonymous")

        now = time.time()
        if tenant_id not in rate_limit_store:
            rate_limit_store[tenant_id] = deque()

        # Drop timestamps outside the window
        window = rate_limit_store[tenant_id]
        while window and window[0] <= now - RATE_LIMIT_WINDOW:
            window.popleft()

        if len(window) >= RATE_LIMIT_THRESHOLD:
            rejected = JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded for {tenant_id}. "
                    f"Max {RATE_LIMIT_THRESHOLD} requests per "
                    f"{RATE_LIMIT_WINDOW}s window."
                },
            )
            _log(rejected, tenant_id, request, start_time)
            return rejected
        window.append(now)

    # Let the endpoint handle the request
    response = await call_next(request)

    # Post-request: latency, usage, structured log
    _log(response, tenant_id, request, start_time)
    return response
