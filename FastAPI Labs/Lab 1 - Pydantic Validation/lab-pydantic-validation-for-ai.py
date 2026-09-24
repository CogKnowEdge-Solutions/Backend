# Import standard typing and FastAPI helpers.
from typing import Literal
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
# Define pre-written replies for our mock LLM.
MOCK_REPLIES = {
    "What's the capital of France?": {
        "role": "assistant",
        "content": "The capital of France is Paris."
    },
    "What's the capital of Germany?": {
        "role": "assistant",
        "content": ""
    }
}
# Mock function called multiple times to simulate LLM replies.
def mock_llm_reply(user_message):
    """Simulates an LLM response by querying a local dictionary lookup."""

    reply = MOCK_REPLIES.get(user_message)

    return reply
# Define the message schema containing role and content.
class Message(BaseModel):
    role: Literal["assistant", "user"]
    content: str = Field(min_length= 1)
# Define incoming request schema with validation bounds.
class ChatRequest(BaseModel):
    messages: Message
    temperature: float = Field(ge=0.0, le=1.0)
    max_tokens: int = Field(gt=0)
# Define outgoing response schema.
class ChatResponse(BaseModel):
    role: str
    content: str = Field(min_length=10)
# Initialize FastAPI application and POST chat endpoint.
app = FastAPI()

@app.post("/chat")
def chat_endpoint(request: ChatRequest):

    user_message = request.messages.content

    # Get raw dictionary response from mock LLM.
    reply = mock_llm_reply(user_message)

    try:
        # Validate reply dict against output schema.
        return ChatResponse(**reply)
    except ValidationError as e:
        # Return standard 500 error structure on validation failure.
        return JSONResponse(
            status_code = 500,
            content = {"error": "response_validation_failed", "detail": e.errors()[0]['msg']}
        )
