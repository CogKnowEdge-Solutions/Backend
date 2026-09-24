from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai import APIStatusError
import asyncio
import os

# Load OPEN_ROUTER_KEY from .env file in the current directory
load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

app = FastAPI()
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
# 401 Unauthorized — the API key was rejected by OpenRouter
@app.exception_handler(LLMAuthError)
async def auth_error_handler(request: Request, exc: LLMAuthError):
    return JSONResponse(
        status_code = status.HTTP_401_UNAUTHORIZED,
        content = {
            "error": "authorization error",
            "message": "Unable to authenticate with OpenRouter API"
        }
    )
# 504 Gateway Timeout — the upstream LLM took too long to respond
@app.exception_handler(LLMTimeoutError)
async def timeout_handler(request: Request, exc: LLMTimeoutError):
    return JSONResponse(
        status_code = status.HTTP_504_GATEWAY_TIMEOUT,
        content = {
            "error": "Request Timed Out",
            "message": "OpenRouter API timed out"
        }
    )
# 502 Bad Gateway — the API call succeeded but the content is unusable (safety block)
@app.exception_handler(LLMSafetyError)
async def safety_error(request: Request, exc: LLMSafetyError):
    return JSONResponse(
        status_code= status.HTTP_502_BAD_GATEWAY,
        content = {
            "error": "unsafe content",
            "message": "unusable content returned"
        }
    )
# 404 Not Found — the model name is invalid or deprecated
@app.exception_handler(BadModelError)
async def bad_model(request: Request, exc: BadModelError):
    return JSONResponse(
        status_code = status.HTTP_404_NOT_FOUND,
        content = {
            "error": "Model Not found",
            "message": "Model name is not valid"
        }
    )
@app.post("/chat")
async def chat(
    message: str,
    deprecated_model: bool = False,
    timeout_error: bool = False,
    bad_key: bool = False,
    unsafe_content: bool= False):
    try:

        # bad_key=True uses a deliberately invalid key to simulate an auth failure
        api = "Invalid_API_Key" if bad_key else api_key
        active_client = AsyncOpenAI(
            api_key=api,
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
            timeout=timeout
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
