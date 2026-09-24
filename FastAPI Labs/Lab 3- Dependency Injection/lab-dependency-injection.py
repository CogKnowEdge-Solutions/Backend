from fastapi import FastAPI, Depends
from typing import Annotated
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

# Load environment variables from .env file
load_dotenv()

# Read the OpenRouter API key from environment
api_key = os.getenv("OPEN_ROUTER_KEY")

# Fallback: prompt for key if not found in environment

# Module-level dictionary to store conversation histories per session
conversation_store = {}

# Create the FastAPI application instance
app = FastAPI()
# Module-level client: built once, shared across all requests
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

async def get_client():
    """Dependency that returns the shared AsyncOpenAI client."""
    return client
async def get_session_id(session_id: str):
    """Pass-through dependency: extracts session_id from query params."""
    return session_id
async def get_session(
    session_id: Annotated[str, Depends(get_session_id)]
):
    """Yield-dependency: provides conversation history for a session.

    Depends on get_session_id — FastAPI resolves that first, then
    passes the result into this function automatically.

    The try/yield/finally structure guarantees the finally block
    runs after the endpoint completes, whether it succeeded or failed.
    """
    # Look up or create the session's history list
    if session_id not in conversation_store:
        conversation_store[session_id] = []

    history = conversation_store[session_id]

    try:
        # Yield the history list to the endpoint
        yield history
    finally:
        # This runs AFTER the endpoint finishes — success or failure
        print(f"[Session {session_id}] request finished.")
@app.post("/chat")
async def chat(
    message: str,
    history: Annotated[list, Depends(get_session)],
    client: Annotated[AsyncOpenAI, Depends(get_client)],
    simulate_error: bool = False
):
    # Append user message BEFORE calling LLM — recorded even on failure
    history.append({
        "role": "user",
        "content": message
    })

    # Prove the client is shared: print its id across multiple calls
    print(f"Client ID: {id(client)}")

    # If simulate_error is True, raise before calling the LLM
    if simulate_error:
        raise ValueError("Simulated Upstream")

    # Call the LLM via the injected client
    response = await client.chat.completions.create(
        model="openrouter/free",
        messages=history
    )

    # Extract the answer and append assistant reply to history
    answer = response.choices[0].message.content
    history.append({
        "role": "assistant",
        "content": answer
    })

    return {
        "answer": answer,
        "history": history
    }
