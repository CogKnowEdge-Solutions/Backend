# Lab 0 Assignment: HTTP Basics for FastAPI

Complete these hands-on tasks after finishing the lab. You will write the
endpoint changes and request payloads yourself — the instructions tell you
what to build and what result to check.

Run the lab notebook through Cell 7 first so `app` and
`client = TestClient(app)` exist. After you edit an endpoint cell, re-run
that cell, then re-run the demo cells so the running `app` picks up the
change.

---

### Task 1 — Name-Search Filter on the Collection

Add a second optional query parameter `q: Optional[str] = None` to the
existing `GET /items` route, alongside `max_price`, and make it return only
the items whose `name` contains `q`, compared case-insensitively (hint:
lowercase both sides before checking for containment). Send
`GET /items?q=note` through `TestClient` and you should receive HTTP 200 with
a list holding only the `Notebook` entry. Then send `q=backpack` and confirm
the result swaps to only the `Backpack`.

---

### Task 2 — A DELETE Endpoint for a Single Item

Add a `DELETE /items/{item_id}` route that removes the matching entry from
`items` and returns `{"detail": "Deleted"}`. Reuse the same path-parameter
shape as the lab's `GET /items/{item_id}` route. Verify through `TestClient`:
call `DELETE /items/1`, then `GET /items`, and confirm the list is one entry
shorter and no longer contains the `Notebook`.
