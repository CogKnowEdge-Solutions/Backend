from fastapi import FastAPI, Depends, APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv()
api_key = os.getenv("OPEN_ROUTER_KEY")
app = FastAPI()
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def get_reply_client():
    return client
class MessageIn(BaseModel):
    message: str

def api_router_level_dep():
    return "This is a apirouter level dependency applied to every end point"

router = APIRouter(dependencies=[Depends(api_router_level_dep)])
@router.post("/message")
async def send_message(payload: MessageIn, replier=Depends(get_reply_client)):
    reply = await replier.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": payload.message}]
    )
    return {"status": "ok", "reply": reply.choices[0].message.content}
@router.post("/apirouter_dependency")
async def show_router_dep(dep_msg=Depends(api_router_level_dep)):
    return {"message": dep_msg}
def moderation_gate(payload: MessageIn):
    if "unsafe" in payload.message.lower():
        raise HTTPException(status_code=400, detail="blocked by moderation")
app.include_router(router, prefix="/public", dependencies=[Depends(moderation_gate)])
app.include_router(router, prefix="/internal")
