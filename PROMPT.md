# The Code Review Prompt

The challenge asks for *"a prompt that reviews short code snippets and recommends three
improvements plus one positive note."* Below is that prompt, standalone and
copy-pasteable into ChatGPT/Claude. The full prototype generalizes it into a scored,
validated, three-step pipeline measured by an eval harness (see `README.md`).

---

## Single-shot prompt (the literal ask)

```
You are a senior code reviewer. Review the Python snippet below BEFORE it reaches a
human reviewer. Be specific and actionable.

Return ONLY JSON with this exact shape:
{
  "summary": "<one sentence overall read>",
  "improvements": [
    {
      "dimension": "readability | structure | maintainability",
      "severity":  "low | medium | high",
      "lines":     [<line number(s)>],
      "issue":     "<what is wrong, stated plainly>",
      "suggestion":"<a concrete fix>"
    }
  ],
  "positive_note": "<one genuine thing the code already does well>"
}

Rules:
- Return EXACTLY three improvements, ordered most-severe first.
- Spread them across readability, structure, and maintainability where the code warrants it.
- Cite the precise line number(s); never flag a line that is genuinely fine.
- A literal assigned to a named constant (e.g. TAX = 0.0825) is NOT a magic number.
- Always check public functions for missing type hints and missing docstrings.
- Output JSON only — no prose, no markdown fences.

Code:
```python
<PASTE SNIPPET HERE>
```
```

---

## How the prototype upgrades this prompt

A single prompt is hard to *measure*. The prototype splits the job into three smaller
prompts — each in `src/prompts.py` — so each step has one job and is independently
improvable:

1. **analyze** — extract neutral structural facts (functions, nesting depth, signals).
2. **critique** — high-recall raw findings per dimension, from a controlled tag vocabulary.
3. **synthesize** — dedupe, rank, assign severity, score each dimension 0–10, write the
   positive note, and emit a schema-validated `ReviewResult` (retry/repair once on bad JSON).

Because the output is a fixed JSON contract, an **eval harness** can score it against
labeled snippets — which is how the prompt rules above (precise lines, named-constant,
type-hints) were *derived from data*, not guessed.
