# Lab 5 Assignment: Security in FastAPI (OAuth2 + JWT)

Complete these hands-on tasks after finishing the lab. You will write the
changes yourself — the instructions tell you what to build and what result
to check.

Run the notebook through Cell 9 first so `app`, `test_client`, `users`,
`create_access_token`, and `oauth2_scheme` all exist. After you edit a
dependency or endpoint, re-run the edited cells plus the cells that created
`get_current_tenant` / `get_session_history` / `chat` (as applicable) before
testing again.

---

### Task 1 — The Admin Gate

Add a `role` claim to the JWT and protect a new endpoint:

1. Give each user a role in the `users` store — `"admin"` for alice,
   `"member"` for bob — and include that role in the payload that
   `create_access_token` signs (so the token carries `sub`, `tenant_id`,
   `role`, and `exp`).
2. Write a `get_current_role` dependency that reuses the same decode-and-catch
   block as `get_current_tenant`, then raises
   `HTTPException(status_code=403, detail="Admin access required")` when the
   `role` claim is not `"admin"`.
3. Add `GET /admin` that depends on `get_current_role` and returns
   `{"message": "admin access granted"}`.

Test all three outcomes:

- alice's token → **Expected:** HTTP `200`.
- bob's token → **Expected:** HTTP `403` with the admin-access detail.
- no token at all → **Expected:** HTTP `401`, rejected by `oauth2_scheme`
  before the role is even examined.

---

### Task 2 — Watching the Form Parser Reject JSON

The `/token` endpoint parses the OAuth2 password grant which is
form-encoded, not JSON. Send alice's exact credentials (`alice` /
`alice-password`) to `/token` as a **JSON body** — use `json=` in the httpx
call instead of `data=`:

- **Expected:** HTTP `422` — FastAPI's form parser cannot extract `username`
  and `password` from a JSON request body, even though the values are correct.
- Contrast this with the lab's working form-data call, which uses `data=`.
  This is the observable reason `python-multipart` is an installation
  requirement and why OAuth2 clients advertise `tokenUrl` for form posts.

---

### Task 3 — Flipping a Character in a Signed Token

Login as alice to get a valid `alice_token`. Copy it and change **one**
character anywhere inside the token string (keep it the same length), then:

1. Send that tampered token to `/chat` in the `Authorization: Bearer ...`
   header with any message and `session_id`.
2. Optionally, also call `jwt.decode(tampered, JWT_SECRET, algorithms=["HS256"])`
   directly and inspect the exception that escapes.

- **Expected (endpoint):** HTTP `401` with the `"Invalid or expired token"`
  detail — the request never reaches `chat()`.
- **Expected (direct decode):** a `PyJWTError` subclass
  (e.g. `InvalidSignatureError`), because the signature is computed over the
  header and payload: altering any character breaks it. This is the same
  mechanism that makes a forged `tenant_id` claim impossible — you cannot
  change what the token says without invalidating its signature.

---

### Task 4 — Isolating Per-User History Within a Tenant

The lab isolates *tenants* from each other with the composite key
`(tenant_id, session_id)`. Two users inside the **same** tenant who pick the
same `session_id` would currently share one history. Fix that:

1. Add a second `tenant-a` user to `users`, e.g. `charlie` / `charlie-password`
   with `tenant_id` set to the same `tenant-a`.
2. Write a dependency that returns the verified identity — the username from
   the `sub` claim plus the `tenant_id`, both read out of the successfully
   decoded payload (the `get_current_user` shape from the assignment's spirit).
3. Change `get_session_history` so the conversation is keyed by a
   **three-component** tuple that includes the verified username, not just
   `(tenant_id, session_id)`.

Verify the isolation:

- Login as alice and as charlie, and have **both** chat on the exact same
  `session_id` string (e.g. `"shared-users"`).
- **Expected:** the two conversations are fully separate — each history
  starts empty and grows only with its own messages, and
  `list(conversation_store.keys())` shows distinct three-component keys for
  the two users. A username is signed into the token, so it is as
  non-forgeable as `tenant_id`.