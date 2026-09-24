# PPT Planning Template — Lab Series Introduction Deck

A reusable outline for planning a short introductory presentation for any technical
lab series. Fill in the placeholders, delete what does not apply, and hand the
result to your preferred slide builder (LLM, designer, or yourself).

## How to use this template

- Work through the 6 slides in order; each one has a **Goal**, a **Framing line**,
  **On-slide content**, and a **Visual note**.
- Replace `<PLACEHOLDER>` values with your series' specifics. Everything else is
  guidance on *what the slide must accomplish*, not final copy.
- Decide the open questions in Section 4 *before* writing slide copy — they change
  what the slides say.
- Respect the Hard Rules in Section 5. They exist because they were violated once
  and had to be fixed.

---

## The 6-slide skeleton

### Slide 1 — The Series, In One Glance

- **Goal:** set expectations and make the payoff concrete in under 10 seconds.
- **Framing line (draft):** "This series takes you from [STARTING POINT] to
  [END RESULT] — one lab at a time."
- **On-slide content:**
  - How many labs + capstones/final projects the series contains
  - What the reader will be able to build by the end (a short list of concrete
    capabilities, not chapter titles)
  - How learning happens (the series' learning loop, e.g. read → run → build)
  - Whether prerequisites exist (if none, say so — it lowers the barrier)
- **Visual note:** hero slide with 3–4 statistic chips (count of labs, tiers,
  target time — only if those are already decided; drop otherwise).

### Slide 2 — The Core Technology, Defined

This slide is the *foundation* the labs assume. Your first lab may jump straight
into a subtopic without ever establishing what the framework/platform actually
is — this slide fixes that gap.

- **Goal:** define the core technology so nothing later feels unexplained.
- **Framing line (draft):** "[TECH] is a [CATEGORY] for [PURPOSE]."
- **On-slide content:**
  - Define the category in one plain sentence (e.g. "an API is an interface on a
    server that other programs call over HTTP")
  - What [TECH] **is** and **does** — its job, not its internals
  - Where it **is used** — real-world situations the reader can picture
  - A closing line tying it to the series: the labs build exactly these
    capabilities on top of it
- **Hard rule:** do NOT leak subtopics that a specific lab teaches (e.g. its data-
  validation library, its auth flow). If Lab 1 covers it, Slide 2 does not.
- **Visual note:** keep it simple — definition + a "where it's used" list. A single
  concept diagram is fine only if it states something Slide 2 actually claims.

### Slide 3 — The Roadmap

- **Goal:** give the reader a mental map of the whole series in one glance.
- **Framing line (draft):** "Same foundation, one new capability per lab."
- **On-slide content:**
  - Group the labs by theme (e.g. Foundations / Async & Real-time / Production
    hardening / Synthesis) — 3 to 4 groups maximum
  - List the **concepts/features** each group covers (not just lab launch titles)
  - Choose one presentation style and stay consistent:
    - **Feature tags** — group name + features it teaches (recommended default)
    - **Lab titles only** — lightest, least informative
    - **Lab numbers + titles** — use only if the reader must know the order
- **Decide in advance:** show lab numbers? difficulty levels? time estimates?
  Default: none of them, unless the content owner explicitly wants them.
- **Visual note:** roadmap, grouped table, or timeline. One row per group, never a
  flat row per lab if the series is long.

### Slide 4 — Anatomy of One Lab

- **Goal:** show what a reader gets with each lab, and how the learning loop works.
- **Framing line (draft):** "Every lab gives you the same [N] things."
- **On-slide content:**
  - Each artifact the series ships, with a one-line "what it's for" (adapt to your
    series — article, notebook, code file, assignment, dataset, environment, etc.)
  - The learning loop those artifacts form (e.g. read → run → build → next lab)
- **Adaptation note:** if the series relies on self-implemented coding tasks,
  describe them as *simple, step-by-step tasks the learner implements themselves*.
  Only mention an absence ("no answer key") if the content owner wants it framed
  that way — usually it is a non-issue and stays unstated.

### Slide 5 — How to Run the Labs

- **Goal:** remove the #1 first-session blocker — "I don't know how to start."
- **Framing line (draft):** "Start by reading the [setup/run guide] — it explains
  how to run everything in this series."
- **On-slide content:**
  - Point to the single setup/run guide that ships with the series; no folder paths
    or navigation (`see the reference file` is enough)
  - The **default path** to run a lab (the one recommended for first timers)
  - The **optional path** (e.g. running it as a real service/server) and when it
    becomes useful
  - If the guide can be re-read at any time, say "pull it up anytime"
- **Hard rule:** do not describe setup mechanics on the slide; that's the guide's
  job. The slide's only job is to route the reader to it.

### Slide 6 — Getting Started

- **Goal:** give a concrete first-week path without over-promising linearity.
- **Framing line (draft):** "Here's the path through the series."
- **On-slide content:**
  - If labs have prerequisites, name exactly which early labs are needed first; the
    rest should be framed honestly — "labs aren't a rigid ladder; each one states
    what it assumes"
  - The recommended starting sequence (read the guide → first lab → warm-up labs →
    heavier labs → final project)
  - Allow for **reordering**: if the content owner plans to re-sequence labs on
    their platform, write this slide to match the *intended* order, and keep the
    numbering loose if it might change
  - A closing hook naming the final build (capstone/final project)
- **Hard rule:** never claim every lab requires the previous one unless it is true.
  Frame as "each lab states what it assumes."

---

## Decisions to settle before writing slide copy

1. **Numbers / difficulty / duration** — may the deck show lab numbers, difficulty
   levels, or time estimates? (Default: none of them.)
2. **Roadmap style on Slide 3** — feature tags, titles only, or numbers + titles?
3. **Order assumptions** — is the series' order firm, or being re-sequenced on the
   platform? Write Slide 6 to match the intended order and keep numbering loose.
4. **Core technology on Slide 2** — which subtopics are reserved for specific labs
   and therefore off-limits on Slide 2?
5. **Artifacts on Slide 4** — which file/asset types does each lab actually ship?
6. **Framing of self-implemented tasks** — how explicit should the "you build it
   yourself" wording be?

## Hard rules (the ones we broke once)

- Don't leak lab-specific subtopics onto the foundation slide.
- Don't omit a clear definition of the core technology just because the first lab
  skips it — the deck is the foundation, not the labs.
- Don't frame the series as a strict prerequisite chain unless it truly is one.
- Don't put setup mechanics on the "how to run" slide — one pointer to the guide.
- Don't show difficulty/duration/numbers unless the content owner opted in.
- Don't hardcode the series' lab numbers into slides if the platform reorders labs
  independently of the repo.
- Keep the deck short — one idea per slide, 6 slides or fewer.

## Sample closing lines

- "By the end, you'll have built [CONCRETE FINAL BUILD]."
- "Every lab ends with something you wrote and ran yourself — that's where it sticks."
- "Pick up the [run guide] anytime; it covers everything."