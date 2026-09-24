from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

app = FastAPI()
class ChatMessage(BaseModel):
    message: str
    simulate_error: bool = False
@app.post("/chat/blocking")
async def chat_blocking(msg: ChatMessage):
    response = await client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": msg.message}],
    )
    return {"answer": response.choices[0].message.content}
async def stream_tokens(message: str, simulate_error: bool = False):
    stream = await client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": message}],
        stream=True,
    )
    event_count = 0
    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                if simulate_error and event_count >= 2:
                    yield "event: error\ndata: Stream interrupted after partial response\n\n"
                    return
                yield f"event: token\ndata: {delta.content}\n\n"
                event_count += 1
    finally:
        await stream.close()
    yield "event: done\ndata: [DONE]\n\n"

@app.post("/chat/stream")
async def chat_stream(msg: ChatMessage):
    return StreamingResponse(
        stream_tokens(msg.message, msg.simulate_error),
        media_type="text/event-stream",
    )
