"""Streamlit UI for the Smart Code Reviewer.

Two tabs:
- Review : paste a Python snippet, run the reviewer, see findings grouped by dimension
           with severity badges, dimension scores, and the positive note.
- Eval   : render the latest harness report (reports/eval_report.md).

Run:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.reviewer import review
from src.schema import Dimension, ReviewResult

REPORTS_DIR = Path(__file__).resolve().parent / "reports"

SEVERITY_BADGE = {"high": "🔴 high", "medium": "🟠 medium", "low": "🟡 low"}
DIMENSION_LABEL = {
    "readability": "Readability",
    "structure": "Structure",
    "maintainability": "Maintainability",
}

SAMPLE = '''\
def process_payment(amount, user):
    api_key = "sk_live_51H8xQ2eZvKYlo"
    total = amount + amount * 0.0825
    if total > 10000:
        total = total - 100
    try:
        return charge(total, api_key)
    except:
        return None
'''

st.set_page_config(page_title="Smart Code Reviewer", page_icon="🔍", layout="wide")
st.title("🔍 Smart Code Reviewer")
st.caption(
    "Structured, scored review across readability, structure, and maintainability — "
    "backed by an evaluation harness."
)

review_tab, eval_tab = st.tabs(["Review", "Eval harness"])


def _render_scores(result: ReviewResult) -> None:
    cols = st.columns(3)
    by_dim = {s.dimension.value: s for s in result.scores}
    for col, dim in zip(cols, [d.value for d in Dimension]):
        score = by_dim.get(dim)
        with col:
            if score is not None:
                st.metric(DIMENSION_LABEL[dim], f"{score.score}/10")
                st.caption(score.rationale)
            else:
                st.metric(DIMENSION_LABEL[dim], "—")


def _render_findings(result: ReviewResult) -> None:
    for dim in [d.value for d in Dimension]:
        items = [f for f in result.findings if f.dimension.value == dim]
        st.subheader(f"{DIMENSION_LABEL[dim]}  ·  {len(items)} finding(s)")
        if not items:
            st.write("_No issues flagged._")
            continue
        for f in items:
            badge = SEVERITY_BADGE.get(f.severity.value, f.severity.value)
            lines = ", ".join(str(n) for n in f.lines) if f.lines else "—"
            with st.expander(f"{badge} · `{f.tag}` · lines {lines} — {f.issue}"):
                st.markdown(f"**Issue:** {f.issue}")
                st.markdown(f"**Suggestion:** {f.suggestion}")


with review_tab:
    code = st.text_area("Paste a Python snippet", value=SAMPLE, height=320)
    if st.button("Run review", type="primary"):
        if not code.strip():
            st.warning("Paste some code first.")
        else:
            try:
                with st.spinner("Reviewing (analyze → critique → synthesize)…"):
                    result = review(code)
            except Exception as exc:
                st.error(f"Review failed: {exc}")
            else:
                st.success(result.summary)
                st.info(f"✅ Positive note: {result.positive_note}")
                _render_scores(result)
                st.divider()
                _render_findings(result)
                with st.expander("Raw ReviewResult JSON"):
                    st.code(result.model_dump_json(indent=2), language="json")

with eval_tab:
    report_path = REPORTS_DIR / "eval_report.md"
    st.caption("Latest run of `python -m harness.run_eval`.")
    if report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.warning(
            "No eval report yet. Run `python -m harness.run_eval` to generate "
            "`reports/eval_report.md`."
        )
