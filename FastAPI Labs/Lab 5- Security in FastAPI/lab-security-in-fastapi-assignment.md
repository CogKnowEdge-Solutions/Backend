# Assignment: Security in FastAPI (OAuth2 + JWT)

This assignment contains 10 exercises testing your understanding of the OAuth2 password flow, JWT structure, stateless authentication, and FastAPI's security dependencies. Complete them without re-running the lab notebook; a few ask you to write small snippets you can run in a scratch file.

---

## Exercises

### Exercise 1: Concept
In this lab, `tenant_id` is read from inside the verified JWT rather than from a query/body field the client sends. What specific attack does that block, and what would happen if the client *could* choose `tenant_id` itself?

### Exercise 2: Concept
`OAuth2PasswordRequestForm` expects which content type and which exact field names? What status code would a client get if it sent JSON like `{"username": "alice", "password": "alice-password"}` to `/token` instead of form data, and why is `python-multipart` in the dependency list?

### Exercise 3: Concept
Contrast a plain server-side session store with this lab's stateless JWT. Where does "who is asking" live in each design, and what becomes non-trivial in the stateless(JWT) design that was trivial with a server-side store — give one concrete example.

### Exercise 4: Concept
Suppose you removed `exp` from the JWT and instead checked expiry by hand with `if payload["exp"] < time.time()`. List two concrete ways that is worse than letting `jwt.decode()` raise `ExpiredSignatureError`. Why does the lab catch the parent type `jwt.PyJWTError` rather than only `ExpiredSignatureError`?

### Exercise 5: Code
Write a `get_current_user` dependency in the same spirit as `get_current_tenant` (Step 5 / Cell 6) that returns a dict `{"username": ..., "tenant_id": ...}` from the decoded payload. It must raise 401 on any `jwt.PyJWTError`.

### Exercise 6: Code
Using `password_hash.verify()` and alice's stored hash `users["alice"]["password_hash"]`, write the two `print(...)` lines that prove a correct password verifies `True` and `"wrong-password"` verifies `False`.

### Exercise 7: Code
Given a valid `alice_token`, write a short snippet that tampers with the token (change one character in its signature section) and then shows `jwt.decode()` rejects it with a `jwt.PyJWTError`.

### Exercise 8: Applied
Two users of the **same** tenant share the same `session_id`. Do they share conversation history in this lab? Answer yes/no and explain precisely why, then propose the smallest change to the composite key that would isolate history per user *within* a tenant.

### Exercise 9: Applied
A support ticket: "User A's follow-up question was answered as if it were their very first message — no context carried over." The composite key is `(tenant_id, session_id)`. Give two concrete causes you would check first, and name the store attribute you would inspect to confirm the diagnosis.

### Exercise 10: Applied
A contractor is fired at 09:00 but their token remains valid until `exp`. JWT is stateless — nothing on the server can "log them out" instantly. Enumerate at least three concrete mitigation strategies, and state the tradeoff each one makes (what it costs, what it fixes).

---

## Answer Key & Explanations

### Exercise 1 Answer
- **Answer**: It blocks **cross-tenant privilege escalation**. The client could set `tenant_id=tenant-b` and read bob's history. With the token design, `tenant_id` is a signed claim: `jwt.decode()` verifies the signature, so a forged value fails and the dependency returns 401 — the request never reaches the history.
- **Explanation**: `get_session_history` derives `tenant_id` from `get_current_tenant`, which only trusts claims that survive signature verification. A query parameter like `session_id` is client-chosen and untrusted; `tenant_id` must never be one. Demo 5's identical `session_id` under two tenants is only the *visible* test — the same mechanism quietly blocks a malicious `tenant_id`.

### Exercise 2 Answer
- **Answer**: Content type `application/x-www-form-urlencoded`, field names `username` and `password`. JSON to `/token` fails FastAPI's form parsing with **422 Unprocessable Entity**. `python-multipart` provides the form parser that `OAuth2PasswordRequestForm` needs; without the package installed, form parsing errors out.
- **Explanation**: "Form data" is the OAuth2 spec's wire format for the password grant. httpx sends it with `data={...}` (as in the login demo cells), not `json={...}`. The `tokenUrl="/token"` advertisement exists precisely so OAuth2-speaking clients know to POST form data there.

### Exercise 3 Answer
- **Answer**: With a server-side store, "who is asking" is a client-chosen `session_id` pointing into the `conversation_store` — identity lives in a server-side lookup table. In this lab it lives **inside the signed token** (`sub`, `tenant_id`), so the server never needs a lookup to know who or which tenant is asking. The non-trivial consequence is **revocation/logout**: with a server-side store you could delete a session row; a valid JWT has no server-side record to remove, so it stays good until `exp`.
- **Explanation**: Statelessness is a trade, not a pure win: authentication becomes cheap and scalable (no per-request DB hit), but "stop trusting this token" requires extra machinery (short lifetimes, denylists, secret rotation — see Exercise 10).

### Exercise 4 Answer
- **Answer**: Two concrete problems with hand-checking: (1) `payload["exp"]` may be **missing** or non-numeric for tokens you never issued — `KeyError`/`TypeError` where you expected a clean 401; (2) it is easy to write the comparison wrong (or `<=` vs `<`, clock skew, no tolerance) and end up accepting expired tokens — the failure mode is silent. The lab catches `jwt.PyJWTError` because it is the **parent** of `ExpiredSignatureError`, `InvalidSignatureError`, and `DecodeError`: one `except` clause turns every failure mode (expired, forged, garbage) into the same 401, instead of needing a separate handler per exception.
- **Explanation**: Demo 8 shows the pay-off: the identical `except jwt.PyJWTError` in `get_current_tenant` handles the expiry demonstration, and the same clause would handle a tampered token. The library owns the check; the code owns the response.

### Exercise 5 Answer
- **Code**:
  ```python
  async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
      try:
          payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
      except jwt.PyJWTError:
          raise HTTPException(status_code=401, detail="Invalid or expired token")
      return {"username": payload["sub"], "tenant_id": payload["tenant_id"]}
  ```
- **Explanation**: Same shape as `get_current_tenant`, but you read an extra claim out of the same verified payload. This is the pattern for growing the "verified identity" object as you add claims (role, scope, ...). An endpoint can then declare `user: Annotated[dict, Depends(get_current_user)]`.

### Exercise 6 Answer
- **Code**:
  ```python
  print(password_hash.verify("alice-password", users["alice"]["password_hash"]))  # True
  print(password_hash.verify("wrong-password", users["alice"]["password_hash"]))  # False
  ```
- **Explanation**: `verify()` takes the plaintext attempt and the stored hash and runs the argon2id computation against it, returning a boolean. The plaintext is never stored or compared directly; even a leaked hash does not reveal the password.

### Exercise 7 Answer
- **Code**:
  ```python
  tampered = alice_token[:-4] + ("abcd" if alice_token[-4:] != "abcd" else "wxyz")
  try:
      jwt.decode(tampered, JWT_SECRET, algorithms=["HS256"])
  except jwt.PyJWTError:
      print("signature check failed: tampered token rejected")
  ```
- **Explanation**: Changing any character of the JWT breaks the HMAC, because the signature is computed over the header+payload. `jwt.decode()` re-computes the signature and raises `InvalidSignatureError` (a `PyJWTError`) before any claim is trusted. This is the same check that rejects a forged `tenant_id`.

### Exercise 8 Answer
- **Answer**: **Yes, they would share history.** The key is `(tenant_id, session_id)`, so two users of the same tenant with the same `session_id` produce the same key and the same list. To isolate per user within a tenant, extend the key to include `sub`: `(tenant_id, sub, session_id)`.
- **Explanation**: What the lab hardens is *tenant* isolation — `tenant_id` is the verified, non-spoofable component of the key. User-level isolation inside a tenant is the same idea one dimension deeper: add the verified username claim (from the same token) as another key component. Demo 5's store keys `[('tenant-a', 'shared-abc'), ('tenant-b', 'shared-abc')]` hint at how a third component would read.

### Exercise 9 Answer
- **Answer**: Two concrete causes to check first:
  1. **User A's token changed or expired between turns** — if the token is new (re-issued) or a different one is used, `get_current_tenant` may return the same tenant but the *history dependency still keys only on `(tenant_id, session_id)`*, so this alone would not empty the history; instead check whether `session_id` itself changed.
  2. **`session_id` was omitted or rotated by the client** — a new/different value means a new key `(tenant_id, new_session_id)`, i.e. a brand-new empty history.
  To confirm: inspect `conversation_store` keys and compare the keys present at each request; the history from the first turn will still exist under the *old* key, so `list(conversation_store.keys())` shows both keys and confirms the client silently changed the identifier.
- **Explanation**: The composite key is unforgiving by design — any change to *either* component starts a new history. That is the same property Demo 5 demonstrates across tenants; here it bites within one user's session because a component changed. (If the token changed but tenant+session were stable, history would *not* reset — which is itself a useful diagnostic.)

### Exercise 10 Answer
- **Answer**: Three mitigations and their tradeoffs:
  1. **Short expirations** (e.g. 15 min, as in the lab's `expires_in_seconds` default) — fixes the *damage window*, not the event: at 09:00 the fired contractor is still valid for up to 15 min. Cheap, stateless, no new infrastructure.
  2. **Server-side denylist/blocklist** keyed by a unique claim such as `jti` (or by `sub`) — fixes *instant* shutdown: the token is rejected the moment it is flagged. Costs are the server-side state JWT was meant to avoid (a lookup per request, needs a store shared across instances in production) and a small check that must happen on every protected request.
  3. **Rotate the signing secret** — instant and *global*: every token in the system dies. Costs: all *legitimate* users must log in again, and you must coordinate secret delivery across services.
- **Explanation**: In a multi-tenant system the common production shape is (1) + (2): short-lived tokens keep the default exposure bounded, and an account-level denylist (checked per request) kills a single compromised/fired user immediately without evacuating everyone. Option (3) is the "nuclear" fallback for a suspected secret leak.

---

*Topical map: Exercises 1–2 → Section 7 (claims + OAuth2PasswordRequestForm); Exercise 3 → Section 7 (statelessness vs server-side store); Exercise 4 → Section 7 (pyjwt exceptions) + Demo 8; Exercises 5–7 → Step 5/Cell 6 patterns; Exercises 8–10 → Section 7 and Demo 5's composite-key proof.*