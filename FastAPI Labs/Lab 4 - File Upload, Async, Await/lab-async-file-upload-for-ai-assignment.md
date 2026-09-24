# Lab 4 Assignment: Async/Await and File Upload for a Document Q&A Pipeline

Complete these hands-on tasks after finishing the lab. You will write the
code changes yourself — the instructions tell you what to build and what
result to check.

Run the notebook through Cell 11 first so `app`, `document_store`, `chunk_text`,
`embed`, `retrieve_top_k`, and `test_client` are all defined. After you edit a
function or endpoint, re-run the edited cells plus the endpoint cells before
testing again. Remember that uploads accumulate: chunks you add to
`document_store` stay there and will be searched by later queries.

---

### Task 1 — Halving the Chunk Size to Watch Scaling

Change the `chunk_size` default in `chunk_text` from 200 to 100 and run the
timing comparison from the lab again — upload the same sample file once with
`sequential=true` and once without it:

1. Record the `chunk_count` and `elapsed_seconds` for both modes. With half the
   chunk size you should now produce roughly twice as many chunks.
2. Compare the two elapsed times with the lab's original numbers.

- **Expected:** the sequential mode's elapsed time roughly doubles (it embeds
  ~twice the chunks one at a time), while the concurrent mode's elapsed time
  stays close to its previous value — `asyncio.gather()` keeps all calls in
  flight together, so more chunks costs little extra wall time.
- The exact seconds will vary with network latency; compare the *trend*, not
  the numbers.

---

### Task 2 — Making Top-K Retrieval Tunable

The `/query` endpoint currently hardcodes the number of retrieved chunks
(`retrieve_top_k(..., k=5)`). Make the number of sources selectable per
request:

1. Add a `k` query parameter to `query()` — give it a sensible default equal
   to the current fixed value so existing behavior is unchanged.
2. Pass that `k` through to `retrieve_top_k` instead of the hardcoded value.
3. Upload any document (your Task 4 text, or the sample file), then call
   `/query` with the same question but different `k` values, e.g. `k=1`,
   `k=3`, and one value larger than the number of stored chunks.

- **Expected:** the length of the `sources` list in the response matches the
  `k` you asked for (capped by however many chunks are stored), and the
  answer is generated from exactly those sources.

---

### Task 3 — Why the Endpoint Must Be `async def`

The lab's `/upload/` endpoint handles awaitable I/O — reading the uploaded
file and embedding. Change the endpoint declaration from `async def upload`
to `def upload` and *do not change the function body*, then re-run the cell
(or reload the notebook code):

- **Expected:** you get a Python `SyntaxError` pointing at an `await` used
  outside an `async` function. You cannot `await` inside a plain `def`.

A path operation that awaits must be declared `async def` — that is the
"door" the lab's concurrency walks through.

---

### Task 4 — Your Own Document Through the Pipeline

Write a short plain-text document of your own — 3 to 5 sentences, 100–200
characters, any topic you know well enough to ask a factual question about.
Then:

1. Upload it through the concurrent `/upload/` endpoint with `TestClient`
   (message the file like the lab does: a filename, your text encoded as
   bytes, and `text/plain` as the content type).
2. Record the returned `chunk_count` and `elapsed_seconds`.
3. Ask `/query` a question that is answerable **only** from the text you wrote
   (something the sample file could not answer).

- **Expected:** the upload returns your `chunk_count` and a concurrent
  `elapsed_seconds`; the query returns an `answer` that draws on your
  document, and the `sources` list contains the chunk(s) of your text that
  match your question.