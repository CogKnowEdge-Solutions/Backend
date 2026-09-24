# Question Generation Guideline (Lab Series → Study Guide)

**Purpose.** Every agent asked to turn a lab series into question-and-answer study
material starts from this file. It captures the process and rules that have been
iterated on and approved: how to propose questions, how to write the study-guide
markdown, and how to generate and verify the HTML equivalent.

**Scope.** This guideline is deliberately lab-agnostic. There must be no references
to any specific lab series, framework, or file. Where a rule says "the reference
document", substitute the template/reference the current task points to.

---

## 1. The Pipeline (non-negotiable order)

Always work in three stages. Never skip ahead:

    Stage 1  present the questions for review  →  iterate with the reviewer, get approval
    Stage 2  write the study guide markdown (.md)
    Stage 3  generate the HTML equivalent from the approved .md

Rules for every stage:

1. **Nothing is finished until reviewed.** A generation without a review pass is
   not a deliverable — it is a draft.
2. **Questions come first.** Present the full question set before writing any
   markdown. If the reviewer wants changes, iterate on the question list only —
   do not silently reflow the md while iterating.
3. **One stage at a time.** Do not write the .md while questions are still
   unapproved, and do not generate HTML until the .md is approved.
4. **Re-verify after every generation.** After each md or HTML generation, run a
   content check against the stage's source before presenting it (see §5).

---

## 2. Stage 1 — Present the Questions for Review

Present questions grouped by section, in document order, each as:

    [Section N] <section name>
      Q<k>. <question text>

Rules:

5. **Cover concepts, not narrative.** Ask about the *concepts and mechanics* the
   labs teach — not the labs' design choices, the story they tell, or their
   step-by-step walkthroughs. The questions test understanding a reader gains
   from the labs.
6. **Pick a representative set.** Choose questions that cover the important ideas
   of the series. Prefer breadth across sections over a deep stack inside one.
7. **One concept per question.** If a topic is compound, split it into separate
   questions. A question must be answerable in a focused way.
8. **Phrase like an instructor.** Use question stems that test understanding:
   - "What does X do?"
   - "Why does Y behave this way?"
   - "How is X different from Y?"
   - "Walk through the life/timeline of Z."
   - "What is the scope/shape of X, and what is it not?"
9. **Order the questions pedagogically.** Within a section, simpler or more
   foundational ideas first, then the ones that build on them.
10. **Every question corresponds to content in the labs.** Do not invent topics
    or examples that the labs do not cover.

---

## 3. Stage 2 — Write the Study Guide Markdown

### 3.1 Document structure

    # <Document Title> — <Series> (Labs X–N)

    <one-paragraph introduction: what this guide is, how to use it>

    Each entry gives you:
    - the **question**, phrased the way an instructor would ask it,
    - a **short answer** to anchor the idea,
    - a plain-language **"let's unpack it"** explanation (with a small code
      snippet wherever the mechanism is clearer in code),
    - and a bold **Key takeaway** to remember.

    ---
    ## 1. <First Section>
    ### Q1. <question text>
    <entry body>
    ---
    ### Q2. <question text>
    ...

Rules:

11. **Title.** Use an em dash between document title and series, en dash in the
    lab range, e.g. `<title> — <series> (Labs 1–12)`. Keep the exact dash style;
    do not normalise it.
12. **Sections.** `## N. <Name>` — numbering is *sequential* (1, 2, 3, ...), never
    reused from lab numbers. Unnumbered trailing sections (if any) stay verbatim.
13. **Questions.** `### Q<N>. <question text>` — continuous numbering across the
    whole document (Q1, Q2, Q3, ...).
14. **Separators.** One `---` between every entry and before every section heading.
15. **Tables.** Use markdown tables for comparisons (e.g. "how many / when / scope"
    matrix per section). Keep them small and readable.

### 3.2 Entry anatomy (every entry, in order)

16. **Short answer** — 1–2 sentences that directly answer the question and anchor
    the concept. Must fully answer every part of the question ("no part left
    unanswered").
17. **"Let's unpack it."** — plain-language explanation. May use bold/italics for
    emphasis and short inline code for identifiers.
18. **Explain, don't state or hand-wave.** Every claim must be *explained* — say
    what it means, why it happens, and what the reader should take from it. Do
    not just assert facts, do not gesture at an idea with "as you'd expect" or
    "which handles this behind the scenes", and never hide behind undefined
    jargon. If a concept has a name, name it, but then unpack it in the next
    sentence in ordinary words.
19. **Simple phrasing, no complex terminology.** Write as your reader has just
    finished the labs and wants to consolidate — not as the marketing page for a
    framework. Prefer short sentences and everyday words over library vocabulary;
    every piece of terminology beyond the essential identifiers must earn its
    place and be explained the first time it is used. If a sentence needs terms
    the reader could not define, rewrite it.
20. **Code snippet** — only where the mechanism is *clearer in code*. Keep it
    minimal, self-contained, and **verbatim from the labs** (never paraphrased,
    abbreviated, or reformatted). If a snippet is long, show the parts that
    matter and let prose carry the rest.
21. **Key takeaway** — one bold sentence: `**Key takeaway:** <one-line rule to remember>`.
    It summarises the answer without repeating it.

Everything in the entry must trace to the labs. Do not introduce claims, numbers,
or examples the labs do not support.

---

## 4. Stage 3 — Generate the HTML Equivalent

Generate one self-contained HTML file from the approved .md, following the
series' HTML conversion guideline and reference document (the header, footer,
code-window shell, and chrome come from the reference; all body content comes
from the .md alone). Leave the .md untouched.

Fidelity rules (hard-won iteration lessons):

22. **Headings verbatim.** h2 and h3 map to the md's `##` and `###` headings
    exactly — same text, same numbering. The converter must NOT renumber headings;
    cross-check the counts against the md (sections and questions).
23. **Code text identical to the md fences.**
    - Escape HTML entities exactly once (`<`, `>`, `&` → `&lt;`, `&gt;`, `&amp;`).
      Never double-escape (`&amp;gt;` renders as literal `&gt;` text and is a bug).
    - Preserve column alignment: runs of 2+ interior spaces become one `&nbsp;`
      **per column** (so aligned comments stay aligned, matching the reference's
      own rendered code).
    - Blank code lines render as a line holding a single `&nbsp;`.
24. **Only intended transformations.** `**Key takeaway:**` becomes the KEY TAKEAWAY
    callout box; markdown list markers become `<li>` items; tables become real
    `<table>` elements; emphasis markers are stripped. Nothing else changes.
25. **Zero leftover markdown.** No `**`, no backticks, no `|`-table pipes, no raw
    `---` as text, no unrendered code-fence or mermaid blocks may remain.
26. **Self-contained.** All assets inline; strict UTF-8 output.

---

## 5. Verification Checklist (run after every generation)

Structural:

- [ ] Every `### Q...` in the md appears as an `<h3>`; counts match.
- [ ] Every `## N...` in the md appears as an `<h2>`; counts match, text equal.
- [ ] Every code fence has exactly one HTML code window; fence body and window
      text are equal (blank `&nbsp;` lines normalised).
- [ ] Number of KEY TAKEAWAY boxes == number of questions.
- [ ] Table count matches the md's comparison tables.
- [ ] One `<h1>` and one `<title>`, identical strings; header/footer present.

Code fidelity:

- [ ] No double-escapes: occurrence count of `&amp;gt;` / `&amp;lt;` is zero.
- [ ] Interior multi-space alignment preserved (`&nbsp;` per column), matching the
      reference's rendered code.

Content:

- [ ] Per-question prose check: md and HTML normalize to equal text (only the
      intended transformations above may differ).
- [ ] No leftover markdown syntax, no `U+FFFD` replacement characters, no
      unrendered mermaid blocks.
- [ ] No invented content — spot-check a sample of claims against the labs.

---

## 6. Deliverable

- Stage 1: the question list, presented for review.
- Stage 2: one `.md` study-guide file.
- Stage 3: one self-contained `.html` file plus the verification results.

Follow the order. Review at every gate. Iterate, then proceed.