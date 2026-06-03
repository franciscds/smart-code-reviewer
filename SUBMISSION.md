# Submission — Code Review Assistant (Challenge #3)

Everything a reviewer needs, in one page.

## 1. 100-word summary

> I built a Code Review Assistant that returns structured, scored feedback—three
> improvement areas plus one positive note—as validated JSON, not free text. The
> differentiator: I also built an evaluation harness. It plants known issues in labeled
> Python snippets and measures, deterministically, how many the reviewer catches per
> dimension, with false-positive traps on clean lines. The reviewer runs an
> analyze→critique→synthesize pipeline through a provider-agnostic client. Iterating
> prompts against the harness moved detection from 75% to 81% recall—88%
> severity-weighted—while driving false positives on clean lines to zero. I shipped the
> reviewer—and the harness that proves it works.

*(100 words.)*

## 2. The prompt

The literal deliverable — a single copy-pasteable prompt that returns three improvements
plus one positive note — is in [`PROMPT.md`](PROMPT.md). The production prompts (the
three-step pipeline) are in [`src/prompts.py`](src/prompts.py).

## 3. The prototype

- **Reviewer:** `analyze → critique → synthesize` (`src/reviewer.py`) → a schema-validated
  `ReviewResult` (`src/schema.py`): `summary`, `findings[]` (dimension, severity, lines,
  issue, suggestion, tag), `scores[]` (0–10 per dimension), `positive_note`.
- **UI:** `streamlit run app.py` — paste a snippet, get findings grouped by dimension with
  severity badges, dimension scores, and the positive note; a second tab renders the
  harness report.
- **Provider-agnostic:** every model call goes through `src/llm_client.py` (one-line vendor swap).

Screenshots: [`docs/ui_review.png`](docs/ui_review.png) (Review tab),
[`docs/ui_eval.png`](docs/ui_eval.png) (Eval harness tab).

## 4. The harness (the headline)

Run: `python -m harness.run_eval`. Latest report: [`reports/eval_report.md`](reports/eval_report.md).

| metric | value |
| --- | --- |
| detection_rate (recall) | **81%** (13/16) |
| severity_weighted_recall | **88%** (23/26) — every high/medium issue caught |
| should_not_flag hits | **0** — never flags a deliberately clean line |

**One iteration that moved the number** (all runs logged in `reports/`):

| run | prompt change | recall | should_not_flag hits |
| --- | --- | --- | --- |
| 1 | baseline | 75% | 3 |
| 2 | cite precise lines + always check type hints/docstrings | 88% | 1 |
| 3 | "a literal assigned to a named constant is not a magic number" | 81% | **0** |

> Note on `false_positive_signal` (~64%): it counts findings beyond the planted labels.
> Inspection showed those were *real* issues the dataset hadn't planted (unused imports, an
> `age == 0` falsy bug, a missing context-manager) — not reviewer errors. The designed
> false-positive measure is **should_not_flag hits = 0**.

## 5. Dataset

Self-created (no confidential data): [`harness/cases/eval_cases.yaml`](harness/cases/eval_cases.yaml)
— 6 Python snippets, 16 planted-and-labeled findings (dimension + tag + severity), plus
clean lines as false-positive traps. Public via the repository link below.

## 6. Links

- **Repository (public link):** _<fill after `gh repo create` / push>_
- **Dataset:** `harness/cases/eval_cases.yaml` in the repo above.
- **Run it:** `pip install -r requirements.txt`, set `ANTHROPIC_API_KEY` in `.env`,
  then `streamlit run app.py` and `python -m harness.run_eval`.

## 7. Submit checklist

- [x] Prototype + prompt (`PROMPT.md`, `app.py`, screenshots in `docs/`)
- [x] 100-word summary (above)
- [x] Public dataset (`eval_cases.yaml`, self-created)
- [ ] Public link (push repo to GitHub — see §6)
