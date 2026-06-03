# Smart Code Reviewer (Harness-First)

An AI assistant that reviews Python for **readability, structure, and maintainability**
before human review — and, more importantly, a **harness that measures whether the
reviewer actually works**.

> I did not just build a reviewer, I built the thing that tells me whether the reviewer works.

## The harness in five lines
1. `harness/cases/eval_cases.yaml` holds Python snippets with **planted, labeled issues** (and clean lines as false-positive traps).
2. The reviewer runs on each snippet and emits a validated `ReviewResult` (JSON).
3. `harness/matcher.py` maps each finding to ground truth by `dimension` + `tag`, line-proximity as tiebreak.
4. `harness/scoring.py` computes **detection_rate**, **false_positive_signal**, and **severity_weighted_recall**, per dimension and overall.
5. `harness/run_eval.py` writes `reports/eval_report.md` (the table below) and `reports/eval_result.json`.

## Latest numbers
6 cases · 16 planted findings · model `claude-sonnet-4-6`. Full table: [`reports/eval_report.md`](reports/eval_report.md).

| metric | value |
| --- | --- |
| detection_rate (recall) | **81%** (13/16) |
| severity_weighted_recall | **88%** (23/26) — every high/medium issue caught |
| should_not_flag hits | **0** — never flags a clean line |

### One iteration that moved the number
The harness drove three prompt changes, each logged in `reports/`:

| run | change | recall | should_not_flag hits |
| --- | --- | --- | --- |
| 1 | baseline prompts | 75% | 3 |
| 2 | cite precise lines + always check type hints / docstrings | 88% | 1 |
| 3 | "a literal assigned to a named constant is not a magic number" | 81% | **0** |

Run 2 lifted recall by making the reviewer thorough; run 3 killed the last false positive
(it had started flagging `TAX = 0.0825` — a *named* constant — as a magic number).

> **Reading `false_positive_signal` (~64%).** This is `unmatched_findings / total_findings`.
> It is high here not because the reviewer is wrong but because it finds **real issues the
> dataset never planted** — unused `os`/`sys` imports, an `age == 0` falsy bug, a missing
> context-manager. We inspected all unmatched findings and they were legitimate. The
> *designed* false-positive measure is **should_not_flag hits (0)**: deliberately clean
> lines the reviewer must not touch.

## Architecture
```
snippet → reviewer.review()  →  ReviewResult (validated JSON)  →  UI  +  Eval harness
            analyze   facts about the code
            critique  raw findings per dimension (high recall)
            synthesize dedupe · rank · score · positive note
```
- **Structured output is the contract** (`src/schema.py`) — UI and harness consume the same shape.
- **Provider-agnostic** — every model call goes through `src/llm_client.py`; swapping vendors is one line.
- **Deterministic where it matters** — matching and scoring are pure Python; only the reviewer calls the model.

## Quickstart
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # then paste your ANTHROPIC_API_KEY into .env

python -m scripts.smoke         # round-trip one prompt
python -m scripts.review_one    # review a sample snippet → ReviewResult
python -m harness.run_eval      # run the harness → reports/
streamlit run app.py            # UI: Review tab + Eval tab
```

## Definition of done
- `streamlit run app.py` reviews a pasted snippet with structured, scored output.
- `python -m harness.run_eval` produces a metrics table over the labeled dataset.
- Zero secrets committed — one `ANTHROPIC_API_KEY` in `.env` (git-ignored).
