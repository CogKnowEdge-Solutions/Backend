# Import helpers for optional values, the app, and the body.
from typing import Optional
from fastapi import FastAPI, Body
# A plain in-memory store. Restarting the server resets it.
items = [
    {"id": 1, "name": "Notebook", "price": 4.99},
    {"id": 2, "name": "Backpack", "price": 39.99},
]
# Create the app and a GET route that can filter by query parameter.
app = FastAPI()

# max_price : Optional[float] = None
#   max_price         -> parameter name; becomes the "?max_price=" query key
#   : Optional[float] -> the value is a number (float) or nothing (None)
#   = None            -> a default, so the client may leave it out entirely
@app.get("/items")
def list_items(max_price: Optional[float] = None):
    if max_price is None:
        return items
    return [item for item in items if item["price"] <= max_price]
# A GET route that reads one item by its path parameter.
# item_id : int
#   item_id -> parameter name; must match the {item_id} in the route path
#   : int   -> FastAPI reads that part of the URL as an integer
@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
# A POST route that reads a JSON body, stores it, and returns it.
# item : dict = Body(...)
#   item        -> parameter name
#   : dict      -> the body arrives as a Python dictionary
#   = Body(...) -> tells FastAPI to read this from the JSON request body
@app.post("/items", status_code=201)
def create_item(item: dict = Body(...)):
    next_id = max(existing["id"] for existing in items) + 1
    item["id"] = next_id
    items.append(item)
    return item
