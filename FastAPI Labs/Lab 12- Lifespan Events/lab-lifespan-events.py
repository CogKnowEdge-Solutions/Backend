from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
import time
def load_index():
    time.sleep(5)
    return {"doc1": "FastAPI is a modern Python web framework",
            "doc2": "Lifespan events run at startup and shutdown",
            "doc3": "app.state stores shared resources across requests"}
def get_index_naive():
    return load_index()

app_naive = FastAPI()

@app_naive.get("/search-naive")
def search_naive(q: str, index=Depends(get_index_naive)):
    if q not in index:
        raise HTTPException(status_code=404, detail="not found")
    return {"query": q, "result": index[q]}
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.index = load_index()
    yield
    app.state.index = None
app = FastAPI(lifespan=lifespan)

def get_index(request: Request):
    return request.app.state.index
@app.get("/search")
def search(q: str, index=Depends(get_index)):
    if q not in index:
        raise HTTPException(status_code=404, detail="not found")
    return {"query": q, "result": index[q]}
