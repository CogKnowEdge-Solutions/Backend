from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from openai import AsyncOpenAI
from collections import deque
import asyncio, os

load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

app = FastAPI()
async def generate(websocket, history):
    stream = await client.chat.completions.create(
        model="openrouter/free",
        messages=history,
        stream=True,
    )
    full_answer = ""
    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_answer += delta.content
                await websocket.send_json({"type": "token", "content": delta.content})
    finally:
        await stream.close()
    return full_answer
async def handle_message(websocket, data, pending_messages):
    pending_messages.append(data)
    await websocket.send_json({"type": "queued", "content": data["content"]})
async def handle_stop(websocket, gen_task):
    gen_task.cancel()
    await websocket.send_json({"type": "cancelled"})
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    history = []
    pending_messages = deque()
    gen_task = None

    try:
        while True:
            if pending_messages:
                data = pending_messages.popleft()
            else:
                data = await websocket.receive_json()

            if data["type"] == "message":
                history.append({"role": "user", "content": data["content"]})
                await websocket.send_json({"type": "status", "content": "generating"})

                gen_task = asyncio.create_task(generate(websocket, history))
                recv_task = asyncio.create_task(websocket.receive_json())

                while True:
                    done, _ = await asyncio.wait(
                        {gen_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if gen_task in done:
                        recv_task.cancel()
                        full_answer = gen_task.result()
                        history.append({"role": "assistant", "content": full_answer})
                        await websocket.send_json({"type": "done", "content": full_answer})
                        break

                    result = recv_task.result()
                    if result["type"] == "stop":
                        await handle_stop(websocket, gen_task)
                        break
                    else:
                        await handle_message(websocket, result, pending_messages)
                        recv_task = asyncio.create_task(websocket.receive_json())

    except WebSocketDisconnect:
        if gen_task and not gen_task.done():
            gen_task.cancel()
