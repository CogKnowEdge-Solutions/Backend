import time
import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from openai import AsyncOpenAI
import numpy as np

# Load OPEN_ROUTER_KEY from .env file in the current directory
load_dotenv()

api_key = os.getenv("OPEN_ROUTER_KEY")

# OpenRouter client: one AsyncOpenAI instance for embeddings and chat
client = AsyncOpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)
def chunk_text(text, chunk_size = 200):
    """Split text into fixed-size chunks with no overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks
async def embed(text):
    """Embed text using the async OpenRouter client."""
    # Use the async client — this is what makes real concurrency possible
    response = await client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=text,
    )
    # response.data is a list; for one input, take the first (and only) item
    return response.data[0].embedding
async def embed_all_sequential(chunks):
    """Embed chunks one at a time. Returns (embeddings, elapsed_seconds)."""
    embeddings = []
    start = time.time()
    for chunk in chunks:
        embedding = await embed(chunk)
        embeddings.append(embedding)
    elapsed = time.time() - start
    return embeddings, elapsed
async def embed_all_concurrent(chunks):
    """Embed all chunks concurrently. Returns (embeddings, elapsed_seconds)."""
    start = time.time()
    # Launch all embed calls at once — they all run in parallel
    embeddings = await asyncio.gather(*[embed(c) for c in chunks])
    elapsed = time.time() - start
    return list(embeddings), elapsed
def cosine_similarity(a, b):
    similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    return similarity
def retrieve_top_k(query_embedding, stored_chunks, k=3):
    """Return the k chunks most similar to the query embedding."""
    scored = []
    for chunk in stored_chunks:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in scored[:k]]
async def generate_answer(question, context_chunks):
    """Generate an answer using retrieved context chunks."""

    context = "\n\n".join([c["text"] for c in context_chunks])
    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer based on the context:"

    response = await client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
# Simple in-memory store — each entry holds a text chunk and its embedding vector
document_store = []

app = FastAPI()

@app.post("/upload/")
async def upload(file: UploadFile, sequential: bool = False):
    """Upload a file and embed its chunks one at a time."""

    text = (await file.read()).decode("utf-8")
    chunks = chunk_text(text)

    if sequential:
        embeddings, elapsed = await embed_all_sequential(chunks)
    else:
        embeddings, elapsed = await embed_all_concurrent(chunks)

    # Store each chunk paired with its embedding
    for chunk_text_val, emb in zip(chunks, embeddings):
        document_store.append({"text": chunk_text_val, "embedding": emb})

    return {"chunk_count": len(chunks), "elapsed_seconds": round(elapsed, 2)}
@app.post("/query")
async def query(question: str):
    """Answer a question using stored document chunks."""
    q_emb = await embed(question)
    top_chunks = retrieve_top_k(q_emb, document_store, k=5)

    answer = await generate_answer(question, top_chunks)

    return {"answer": answer, "sources": [c["text"] for c in top_chunks]}
