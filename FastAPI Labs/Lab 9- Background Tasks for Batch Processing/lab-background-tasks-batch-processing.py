from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os, uuid

load_dotenv()
api_key = os.getenv("OPEN_ROUTER_KEY")
client = AsyncOpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
app = FastAPI()
job_store: dict[str, dict] = {}

def generate_job_id():
    return uuid.uuid4().hex
async def summarize_single_review(review_text):
    response = await client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": f"Summarize this customer review in one or two sentences: {review_text}"}],
    )
    return response.choices[0].message.content
async def run_batch_summary(job_id, reviews, simulate_failure=False):
    job_store[job_id]["status"] = "running"
    try:
        for index, review in enumerate(reviews):
            if simulate_failure and index == 1:
                raise RuntimeError("Simulated failure on review 2")
            summary = await summarize_single_review(review)
            job_store[job_id]["results"].append(summary)
            job_store[job_id]["completed"] += 1
        job_store[job_id]["status"] = "done"

    except Exception as exc:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(exc)
class BatchRequest(BaseModel):
    reviews: list[str]
    simulate_failure: bool = False

@app.post("/tasks/summarize-batch")
async def summarize_batch(req: BatchRequest, background_tasks: BackgroundTasks):
    job_id = generate_job_id()
    job_store[job_id] = {"status": "pending", "total": len(req.reviews), "completed": 0, "results": [], "error": None}
    background_tasks.add_task(run_batch_summary, job_id, req.reviews, req.simulate_failure)
    return {"job_id": job_id, "status": "pending", "total": len(req.reviews)}

@app.get("/tasks/{job_id}")
async def get_task(job_id: str):
    return job_store.get(job_id, {"error": f"Job {job_id} not found"})
