from fastapi import (
    FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, APIRouter,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, ValidationError
from typing import Annotated, Literal
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collections import deque
import jwt, os, time, asyncio, json, contextlib

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

# Lab-only convenience default. In production, always read from env/secrets manager.
JWT_SECRET = os.getenv("JWT_SECRET", "lab13-dev-secret-not-for-production")
class GenerateMessage(BaseModel):
    type: Literal["generate"]
    topic: str = Field(min_length=1, description="The content topic to generate about")
    simulate_failure: bool = Field(default=False, description="If True, the pipeline fails at the review step")

class SuggestionMessage(BaseModel):
    type: Literal["suggestion"]
    content: str = Field(min_length=1, description="A steering instruction incorporated at the next checkpoint")
connection_registry: dict[str, WebSocket] = {}
suggestions: dict[str, deque] = {}
class PreferencesStore:
    def __init__(self):
        self.is_loaded = False
        self.data: dict[str, dict] = {}

async def load_tenant_preferences():
    """Simulates a slow database/index load — the reason lifespan exists here."""
    await asyncio.sleep(2)
    return {
        "tenant-a": {"tone": "professional", "length": "medium", "style": "blog"},
        "tenant-b": {"tone": "casual", "length": "short", "style": "social"},
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    app.state.llm_client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    prefs = PreferencesStore()
    prefs.data = await load_tenant_preferences()
    prefs.is_loaded = True
    app.state.tenant_preferences = prefs
    yield
    # --- shutdown ---
    app.state.tenant_preferences.is_loaded = False

app = FastAPI(lifespan=lifespan)
# Hardcoded users for this demo. In production, hashed passwords live in a database.
users = {
    "alice": {"tenant_id": "tenant-a"},
    "bob":   {"tenant_id": "tenant-b"},
}

def create_token(username: str, tenant_id: str) -> str:
    payload = {
        "sub": username,
        "tenant_id": tenant_id,
        "exp": time.time() + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def _extract_tenant_from_headers(headers) -> str:
    """Read the Authorization header, decode the JWT, return tenant_id."""
    auth = headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = auth[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["tenant_id"]

async def get_current_tenant(
    request: Request = None,
    websocket: WebSocket = None,
) -> str:
    """Extract tenant_id from either an HTTP request or a WebSocket connection.

    FastAPI injects Request for HTTP routes and WebSocket for WS routes.
    Accepting either with a default of None lets one function cover both.
    """
    source = request or websocket
    if source is None:
        raise HTTPException(status_code=401, detail="No request context")
    return _extract_tenant_from_headers(source.headers)
auth_router = APIRouter()

@auth_router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = users.get(form_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(form_data.username, user["tenant_id"])
    return {"access_token": token, "token_type": "bearer"}

app.include_router(auth_router, prefix="/auth")
content_router = APIRouter()
async def llm_generate(client: AsyncOpenAI, prompt: str) -> str:
    """Send a prompt to the LLM and return the response text."""
    resp = await client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()

async def push_to_tenant(tenant_id: str, message: dict):
    """Send a message to the tenant's WebSocket if connected. Fails safely if not."""
    ws = connection_registry.get(tenant_id)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            pass  # Connection closed unexpectedly — don't crash the pipeline

def pull_suggestions(tenant_id: str) -> list[str]:
    """Return and clear the tenant's pending suggestions."""
    pending = list(suggestions.get(tenant_id, []))
    suggestions[tenant_id] = deque()
    return pending
async def generate_titles(client: AsyncOpenAI, topic: str) -> list[str]:
    """Generate 3 candidate titles concurrently using asyncio.gather()."""
    prompts = [
        f"Give me one short, catchy article title about: {topic}",
        f"Give me one informative article title about: {topic}",
        f"Give me one engaging blog post title about: {topic}",
    ]
    return await asyncio.gather(*[llm_generate(client, p) for p in prompts])

async def run_pipeline(tenant_id: str, topic: str, simulate_failure: bool):
    client: AsyncOpenAI = app.state.llm_client
    prefs: PreferencesStore = app.state.tenant_preferences
    tenant_prefs = prefs.data.get(tenant_id, {})

    try:
        # --- Step A: Announce, then generate titles concurrently ---
        await push_to_tenant(tenant_id, {"type": "progress", "step": "generating titles"})
        titles = await generate_titles(client, topic)
        chosen_title = titles[0]

        # --- Step B: Announce the chosen title (first checkpoint window is now closed) ---
        await push_to_tenant(tenant_id, {
            "type": "progress",
            "step": "titles generated",
            "chosen_title": chosen_title,
        })

        # --- Step C: Checkpoint 1 — fold in suggestions sent during title generation ---
        pending = pull_suggestions(tenant_id)
        suggestion_text = "\n".join(pending) if pending else "None"

        draft_prompt = (
            f"Write a short article draft titled '{chosen_title}'. "
            f"Tone: {tenant_prefs.get('tone', 'neutral')}. "
            f"Length: {tenant_prefs.get('length', 'medium')}. "
            f"Style: {tenant_prefs.get('style', 'blog')}. "
        )
        if pending:
            draft_prompt += f" Begin with the exact phrase of this user suggestion: {suggestion_text}"
        draft = await llm_generate(client, draft_prompt)

        # --- Step D: Announce the draft (second checkpoint window is now closed) ---
        await push_to_tenant(tenant_id, {"type": "progress", "step": "draft complete"})

        # --- Step E: Checkpoint 2 — suggestions that arrived while drafting get a review pass ---
        new_suggestions = pull_suggestions(tenant_id)

        if simulate_failure:
            raise RuntimeError("Simulated pipeline failure during review step")

        if new_suggestions:
            review_prompt = (
                f"Review and improve this draft based on the feedback: {new_suggestions}. "
                f"If it already covers the feedback, keep it. Draft: {draft}"
            )
            draft = await llm_generate(client, review_prompt)
            await push_to_tenant(tenant_id, {
                "type": "progress",
                "step": "review complete",
                "feedback": new_suggestions,
            })

        # --- Step F: Done ---
        await push_to_tenant(tenant_id, {"type": "done", "content": draft})

    except Exception as exc:
        await push_to_tenant(tenant_id, {"type": "error", "content": str(exc)})
@content_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    tenant_id: Annotated[str, Depends(get_current_tenant)],
):
    await websocket.accept()
    connection_registry[tenant_id] = websocket
    suggestions[tenant_id] = deque()

    await websocket.send_json({"type": "hello", "content": f"registered as {tenant_id}"})
    try:
        while True:
            data = await websocket.receive_json()
            try:
                if data["type"] == "generate":
                    msg = GenerateMessage(**data)
                    asyncio.create_task(run_pipeline(tenant_id, msg.topic, msg.simulate_failure))
                    await websocket.send_json({"type": "accepted", "topic": msg.topic})
                elif data["type"] == "suggestion":
                    msg = SuggestionMessage(**data)
                    suggestions[tenant_id].append(msg.content)
                    await websocket.send_json({"type": "ack", "content": msg.content})
                else:
                    raise ValueError(f"Unknown message type: {data['type']}")
            except (ValidationError, KeyError, ValueError) as exc:
                await websocket.send_json({"type": "error", "content": f"Invalid message: {exc}"})
    except WebSocketDisconnect:
        connection_registry.pop(tenant_id, None)

app.include_router(content_router, prefix="/content")
