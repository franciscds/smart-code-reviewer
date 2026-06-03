# CLAUDE.md — Working conventions for Smart Code Reviewer

Read this before touching code. This is a **harness-first** project: the eval harness
is the backbone, the reviewer is iterated to move harness metrics — never by vibes.

## Layout
```
src/        reviewer pipeline + contracts + LLM client
  schema.py       Pydantic data contracts (the JSON contract)
  llm_client.py   provider-agnostic model wrapper (LLMClient.complete)
  prompts.py      system/user prompts for analyze / critique / synthesize
  reviewer.py     review() = analyze -> critique -> synthesize
harness/    deterministic evaluation
  cases/eval_cases.yaml   labeled snippets (ground truth + false-positive traps)
  matcher.py      map reviewer findings -> expected findings
  scoring.py      detection_rate, false_positive_signal, severity_weighted_recall
  run_eval.py     run all cases, write reports/
reports/    eval_report.md (human) + eval_result.json (machine)
app.py      Streamlit UI (Review tab + Eval tab)
scripts/    smoke.py and helpers
```

## Rules
1. **Structured output is the contract.** The reviewer emits a validated `ReviewResult`
   (`src/schema.py`), never free text. UI and harness consume the same schema.
2. **Provider-agnostic.** All model calls go through `LLMClient`. Swapping providers is
   a one-line change. Do not import `anthropic` outside `src/llm_client.py`.
3. **Deterministic where it matters.** Matching and scoring are pure, inspectable Python.
   Only `reviewer.py` calls the model.
4. **Controlled tag vocabulary.** `Finding.tag` is what the harness matches. Tags must come
   from the vocabulary in `harness/cases/eval_cases.yaml` (and `src/prompts.py`).
5. **Iterate against the harness.** To improve the reviewer, run the harness, read
   `reports/eval_report.md`, fix the prompt, re-run. Log each run.

## Commands
```
python -m scripts.smoke        # Phase 1: round-trip one prompt
python -m scripts.review_one   # Phase 2: review a sample snippet, print ReviewResult
python -m harness.run_eval     # Phase 3+: run the eval harness, write reports/
streamlit run app.py           # Phase 5: UI
```

## Secrets
One `ANTHROPIC_API_KEY` in `.env` (copied from `.env.example`). Never commit `.env`.
