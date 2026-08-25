# Assignment: Async/Await and File Upload for a Document Q&A Pipeline

This assignment contains 6 exercises designed to test your understanding of async concurrency in FastAPI, the `asyncio.gather()` pattern, and the document Q&A pipeline. Complete these exercises without re-running the lab notebook.

---

## Exercises

### Exercise 1: Concept
Why does calling the **synchronous** Google GenAI client (`client.models.embed_content`) instead of the **async** client (`client.aio.models.embed_content`) inside an `async def` function eliminate the concurrency benefit? What happens at the execution level?

### Exercise 2: Concept
What does `asyncio.gather()` actually wait for? If you launch 8 embedding calls with `asyncio.gather()`, does it wait for each call to finish one at a time, or does it wait for all of them to finish? Explain in one or two sentences.

### Exercise 3: Code
The `retrieve_top_k` function currently returns the top 3 most similar chunks (`k=3`). Write the modified function signature and the single line that changes to return the top 5 instead. What effect would this have on the `generate_answer` function's input?

### Exercise 4: Code
If you changed the upload endpoint from `async def upload` to `def upload` (removing `async`), what would happen to the timing comparison between sequential and concurrent? Would the concurrent endpoint still show a speedup? Explain briefly.

### Exercise 5: Applied
Write a short sample text of your own (3-5 sentences about any topic you choose). Then describe the exact steps you would take to:
1. Upload it via `/upload/` (concurrent) using TestClient
2. Query it via `/query` with a relevant question
3. What output would you expect to see?

You do not need to actually run the code — just write the Python code you would use.

### Exercise 6: Concept
FastAPI runs `def` path operations in a threadpool but runs `async def` path operations directly on the event loop. In which scenario would using `def` (threadpool) be the better choice for a path operation — an endpoint that does heavy CPU computation, or an endpoint that makes 10 sequential API calls? Justify your answer.

---

## Answer Key & Explanations

### Exercise 1 Answer
*   **Explanation**: The synchronous client (`client.models.embed_content`) blocks the current thread until the API call completes. Even though the endpoint is `async def` and running on the event loop, calling a blocking (synchronous) function inside it blocks the event loop itself. This means no other coroutine can make progress while the sync call is in flight — you get the worst of both worlds: you lose the threadpool benefit of `def` and the concurrency benefit of `async def`. The event loop is frozen waiting for each sync call to return, so all calls run sequentially just as they would in a plain `def` function. The async client (`client.aio.models.embed_content`) is a true coroutine that yields control back to the event loop while waiting for the network response, allowing other tasks to run.

### Exercise 2 Answer
*   **Answer**: `asyncio.gather()` starts all the coroutines at once on the event loop and then waits for **all of them to complete**. It does not wait for each one individually — it launches them all, and once every single one has finished, it returns a list of all their results. The total wait time is close to the duration of the slowest single call.

### Exercise 3 Answer
*   **Modified signature and line**:
    ```python
    def retrieve_top_k(query_embedding, stored_chunks, k=5):
    ```
    The only change is `k=3` becomes `k=5` in the function signature default.
*   **Effect on generate_answer**: The `generate_answer` function would receive 5 context chunks instead of 3. This means the LLM prompt would contain more context, which could improve answer quality (more information to draw from) but also increase token usage and cost. The prompt might become too long if the chunks are large.

### Exercise 4 Answer
*   **Explanation**: If the upload endpoint used `def` instead of `async def`, it would run in a threadpool. The `await embed(chunk)` calls inside it would still work (Starlette handles this), but the sequential mode would still be sequential — each call blocks its thread until the response arrives. The concurrent mode would still use `asyncio.gather()` and still show a speedup. The timing comparison would still work, though the absolute times might differ slightly because threadpool execution has slightly different scheduling characteristics than direct event-loop execution.

### Exercise 5 Answer
*   **Sample text** (example):
    ```python
    MY_TEXT = """Machine learning is a subset of artificial intelligence
    that enables systems to learn from data. Neural networks are inspired
    by the structure of the human brain. Training a model requires large
    datasets and significant computational resources."""
    ```
*   **Upload code**:
    ```python
    files = {"file": ("mytext.txt", MY_TEXT.encode(), "text/plain")}
    result = test_client.post("/upload/", files=files)
    print(result.json())
    ```
*   **Query code**:
    ```python
    query_result = test_client.post("/query?question=What are neural networks inspired by?")
    print(query_result.json())
    ```
*   **Expected output**: The upload should return a `chunk_count` (depends on text length at `chunk_size=200`) and `elapsed_seconds`. The query should return an `answer` referencing the brain structure inspiration, plus `sources` containing the relevant chunk(s) from the uploaded text.

### Exercise 6 Answer
*   **Answer**: An endpoint that does **heavy CPU computation** would be the better candidate for `def` (threadpool). CPU-bound work does not benefit from `async def` because it never yields control to the event loop — it just runs continuously. Putting it in a threadpool means it runs on a separate thread, leaving the event loop free to handle other requests. An endpoint making 10 sequential API calls is the classic use case for `async def` + `asyncio.gather()` — the API calls are I/O-bound and can be concurrent.
