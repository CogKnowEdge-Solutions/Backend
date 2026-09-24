# Lab Assignment Guidelines

How to write `labX-assignment.md` files from a finished lab guide. These rules are lab-agnostic — they apply to any hands-on lab whose `labX.md` ends with an "Optional Exercise" section and whose step-by-step instructions form the taught material.

---

## Goal

Replace a lab's question-and-answer assignment (exercises + answer key) with a short, hands-on, coding-only task list. The reader proves they understood the lab by doing small amounts of **new work** — not by reciting what the lab said.

---

## Task Count: 3 Minimum, 5 Maximum

- **5 tasks** if the lab is very easy, quick to execute, low time cost, and needs little to no reasoning.
- **3 tasks** if the lab is substantial — not necessarily *difficult*, just with enough real content (multiple demos, several distinct taught concepts).
- Count the concepts the lab actually taught before fixing the number. More separate, trainable concepts → more tasks (up to 5); fewer or heavily-overlapping concepts → 3.

---

## Hard Rules

These are absolute; the rest of this document elaborates them.

1. **No answer key. No theory / reasoning-only exercises.** Every task must be something the reader *does* in the running stack. If a lab concept exists only as prose ("think about why X"), strip the question and keep only the piece that is observable or executable.
2. **Task 1 is always the lab's "Optional Exercise"**, rewritten hands-on-first and given its **own descriptive name** (e.g. "A Correlation in the Other Direction"). Never call it "The Optional Exercise".
3. **One task, one thing.** A task covers exactly one concept. It may bundle steps only when they are directly related (setup + the single observation it feeds).
4. **Reinforce, never re-run.** Tasks must be **new work** — not a verbatim repeat of the lab's steps. A same-shape query against a *different* dimension is acceptable only when it is the same concept and directly related; verify the lab's own demos first so you don't assign what the lab already did.
5. **Reinforce only what that lab taught.** Do not pull concepts from later labs. Do not invent new syntax.
6. **Queries are hints, never pasted answers.** Give the piece-parts (metric names, function names, labels, operators, windows, aggregation shape) and let the reader assemble the query. Operational/action commands (`docker compose ...`, curl traffic loops, admin POSTs) may be given verbatim — they are setup, not answers.
7. **No recycling across labs.** Once a task variation is used in one lab's assignment, don't reuse it in another lab's.

---

## Writing Conventions

### Structure

```markdown
# Lab N Assignment: <Title>

Complete these hands-on tasks after finishing the lab. You will write
the <PromQL|LogQL|...> queries yourself — the hints tell you what to build.

[keep the traffic loops from Steps X–Y running]

---

### Task 1 — <Descriptive Name of the Renamed Optional Exercise>

<Short paragraph: set-up, the action, the expected/verified outcome.>

---

### Task 2 — <Name>

...
```

- Tasks separated by `---`.
- Each task: one paragraph, a setup line (what to run/do first), an action, and the outcome to check.
- Mention the traffic loops / failure flags the task depends on, if any.
- No comments, no emoji, no fluff.

### Hint style

For a timed-series / log query, hint the shape without assembling it:

> A `rate()` of `http_requests_total`, with a label selector on `endpoint`, counting over a 5-minute window.

Not:

> `sum(rate(http_requests_total{endpoint="/work"}[5m]))`

### Determinism

Never leave decisions to data the reader hasn't seen.

- If a task needs a filter string, tell them to **copy a substring from a line they actually see** — never "pick something that looks good".
- If a task depends on which containers write stdout or which labels exist, **verify against the compose file and the agent config first** and state the exact container / label.
- Every task must have a checkable "you should see" outcome.

---

## Verification Before You Write

- Re-read the lab's step-by-step section and note every concept the demos actually exercised — these are the candidates for reinforcement tasks.
- Check the lab's own text before assigning "new" work: if the lab states a finding parenthetically, that observation is already covered — find a different angle or skip it.
- Check the config files (`docker-compose.yml`, relabel/agent configs, rule files): confirm which labels exist, which services log to stdout, which thresholds the rules use.
- Check your earlier labs' assignments so you don't duplicate a task.
- Flag any borderline/redundant task explicitly in the plan — let the owner decide rather than silently including it.

---

## Workflow

One lab at a time:

1. Read `labX-assignment.md` (old questions + answer key) and `labX.md` (concepts + steps + Optional Exercise).
2. Draft the task plan (Task 1 = renamed Optional Exercise, then 2–4 reinforcement tasks). Include proposed titles and one-line descriptions.
3. **Present the plan and wait for explicit approval. Do not edit the file before approval.**
4. On approval, rewrite only that lab's assignment file.
5. Note per-lab decisions (dropped tasks and why) for the record.

---

## Common Traps (Learned the Hard Way)

- **"It's basically the same as the lab"** — a task that redoes a demo step, even with better wording, is a copy. Change the dimension, the aggregation, the direction, or drop the task.
- **Theory hidden inside a hands-on task** ("then reason about why...") — cut the reasoning clause, keep the observation.
- **Optional-exercise drift** — keep the optional's practical outcome intact when renaming it; only the name and any theory clauses change.