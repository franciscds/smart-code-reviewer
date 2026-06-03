"""Run the eval harness over all labeled cases and write reports/.

    python -m harness.run_eval                  # full run
    python -m harness.run_eval --limit 2         # quick iteration on the first 2 cases
    python -m harness.run_eval --judge           # enable the LLM-as-judge matcher (stretch)

Writes:
    reports/eval_report.md     human-readable table (goes in the submission + demo)
    reports/eval_result.json   machine-readable, includes raw findings per case
Prints the aggregate detection rate.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from harness.matcher import ExpectedFinding, match
from harness.scoring import DIMENSIONS, aggregate, score_case
from src.llm_client import LLMClient
from src.reviewer import Reviewer
from src.schema import Finding

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "harness" / "cases" / "eval_cases.yaml"
REPORTS_DIR = ROOT / "reports"


def _pct(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def load_cases(path: Path) -> List[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["cases"]


def make_llm_judge(client: LLMClient):
    """Optional semantic matcher: returns True if a finding is the same issue as expected."""

    def judge(finding: Finding, expected: ExpectedFinding) -> bool:
        out = client.complete(
            system="You answer with exactly 'yes' or 'no'.",
            user=(
                "Do these describe the SAME code issue?\n"
                f"Reviewer: [{finding.dimension.value}/{finding.tag}] {finding.issue}\n"
                f"Expected: [{expected.dimension}/{expected.tag}] (lines {expected.lines})\n"
                "Answer yes or no."
            ),
            max_tokens=5,
        )
        return out.strip().lower().startswith("y")

    return judge


def run(limit: Optional[int] = None, use_judge: bool = False) -> dict:
    cases = load_cases(CASES_FILE)
    if limit:
        cases = cases[:limit]

    client = LLMClient()
    reviewer = Reviewer(client=client)
    judge = make_llm_judge(client) if use_judge else None

    case_scores: List[dict] = []
    case_records: List[dict] = []

    for case in cases:
        cid = case["id"]
        expected = [ExpectedFinding.from_dict(e) for e in (case.get("expected_findings") or [])]
        snf = case.get("should_not_flag") or []
        print(f"  reviewing {cid} ...", flush=True)
        try:
            result = reviewer.review(case["code"])
            findings: List[Finding] = result.findings
            summary = result.summary
            positive = result.positive_note
        except Exception as exc:  # one bad case must not kill the run
            print(f"    ! review failed: {exc}")
            findings, summary, positive = [], f"ERROR: {exc}", ""

        m = match(findings, expected, should_not_flag=snf, judge=judge)
        score = score_case(m, findings, expected)
        case_scores.append(score)
        case_records.append(
            {
                "id": cid,
                "description": case.get("description", ""),
                "score": score,
                "missed": [
                    {"dimension": e.dimension, "tag": e.tag, "severity": e.severity, "lines": e.lines}
                    for e in m.missed
                ],
                "findings": [f.model_dump(mode="json") for f in findings],
                "summary": summary,
                "positive_note": positive,
            }
        )

    agg = aggregate(case_scores)
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model": client.model,
        "num_cases": len(cases),
        "aggregate": agg,
        "cases": case_records,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "eval_result.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (REPORTS_DIR / "eval_report.md").write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict) -> str:
    agg = report["aggregate"]
    out: List[str] = []
    out.append("# Eval Report — Smart Code Reviewer\n")
    out.append(
        f"_Generated: {report['generated_at']} · model: `{report['model']}` · "
        f"cases: {report['num_cases']}_\n"
    )

    out.append("## Aggregate\n")
    out.append("| metric | value |")
    out.append("| --- | --- |")
    out.append(
        f"| detection_rate (recall) | **{_pct(agg['detection_rate'])}** "
        f"({agg['matched']}/{agg['total_expected']}) |"
    )
    out.append(
        f"| severity_weighted_recall | {_pct(agg['severity_weighted_recall'])} "
        f"({agg['weighted_matched']}/{agg['weighted_total']}) |"
    )
    out.append(
        f"| false_positive_signal | {_pct(agg['false_positive_signal'])} "
        f"({agg['unmatched_findings']}/{agg['total_findings']}) |"
    )
    out.append(f"| should_not_flag hits | {agg['should_not_flag_hits']} |\n")

    out.append("## By dimension\n")
    out.append("| dimension | detection_rate | false_positive_signal |")
    out.append("| --- | --- | --- |")
    for dim in DIMENSIONS:
        d = agg["by_dimension"][dim]
        out.append(
            f"| {dim} | {_pct(d['detection_rate'])} ({d['matched']}/{d['total_expected']}) "
            f"| {_pct(d['false_positive_signal'])} ({d['unmatched_findings']}/{d['total_findings']}) |"
        )
    out.append("")

    out.append("## Per case\n")
    out.append("| case | expected | matched | recall | findings | fp_signal | snf hits |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for rec in report["cases"]:
        s = rec["score"]
        out.append(
            f"| {rec['id']} | {s['total_expected']} | {s['matched']} "
            f"| {_pct(s['detection_rate'])} | {s['total_findings']} "
            f"| {_pct(s['false_positive_signal'])} | {s['should_not_flag_hits']} |"
        )
    out.append("")

    misses = [(rec["id"], m) for rec in report["cases"] for m in rec["missed"]]
    out.append("## Misses — what to fix next\n")
    if not misses:
        out.append("_None. Every expected finding was caught._\n")
    else:
        for cid, m in misses:
            out.append(
                f"- **{cid}**: {m['dimension']}/{m['tag']} "
                f"({m['severity']}) lines {m['lines']}"
            )
        out.append("")

    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Smart Code Reviewer eval harness.")
    parser.add_argument("--limit", type=int, default=None, help="run only the first N cases")
    parser.add_argument("--judge", action="store_true", help="enable LLM-as-judge matcher")
    args = parser.parse_args()

    print("Running eval harness ...")
    report = run(limit=args.limit, use_judge=args.judge)
    agg = report["aggregate"]
    print(
        f"\nAggregate detection_rate: {_pct(agg['detection_rate'])} "
        f"({agg['matched']}/{agg['total_expected']}) · "
        f"false_positive_signal: {_pct(agg['false_positive_signal'])} · "
        f"snf hits: {agg['should_not_flag_hits']}"
    )
    print(f"Wrote {REPORTS_DIR / 'eval_report.md'} and {REPORTS_DIR / 'eval_result.json'}")


if __name__ == "__main__":
    main()
