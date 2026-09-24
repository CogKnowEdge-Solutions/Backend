from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import Annotated
import jwt
import os
import time

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

# Production rule: JWT secret from env/secrets manager, NEVER hardcoded.
# The default is a lab-only convenience so the notebook runs as-is.
JWT_SECRET = os.getenv("JWT_SECRET", "lab5-dev-only-secret-not-for-production")

conversation_store = {}   # keys are (tenant_id, session_id) tuples
app = FastAPI()

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

users = {
    "alice": {
        "password_hash": password_hash.hash("alice-password"),
        "tenant_id": "tenant-a",
    },
    "bob": {
        "password_hash": password_hash.hash("bob-password"),
        "tenant_id": "tenant-b",
    },
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def create_access_token(username, tenant_id, expires_in_seconds=1800):
    payload = {
        "sub": username,
        "tenant_id": tenant_id,
        "exp": time.time() + expires_in_seconds,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    stored = users.get(form_data.username)
    # Timing guard: ALWAYS run one argon2 verify, even for unknown usernames,
    # so response time cannot reveal which accounts exist.
    target = stored["password_hash"] if stored else users["alice"]["password_hash"]
    valid_password = password_hash.verify(form_data.password, target)

    if not stored or not valid_password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token(form_data.username, stored["tenant_id"])
    return {"access_token": token, "token_type": "bearer"}

async def get_current_tenant(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["tenant_id"]

async def get_session_history(
    tenant_id: Annotated[str, Depends(get_current_tenant)],
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
    client: Annotated[AsyncOpenAI, Depends(get_client)],
):
    history.append({"role": "user", "content": message})

    response = await client.chat.completions.create(
        model="openrouter/free",
        messages=history,
    )

    answer = response.choices[0].message.content
    history.append({"role": "assistant", "content": answer})

    return {"answer": answer, "history": history}
