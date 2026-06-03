"""Deterministic scoring over matched findings.

Metrics (per dimension and overall):
- detection_rate (recall)        = matched_expected / total_expected
- false_positive_signal          = unmatched_findings / total_findings   (lower is better)
- severity_weighted_recall       = weighted matched / weighted total   (high=3, med=2, low=1)

Rates are never averaged; we aggregate raw counts and divide once, so cases with many
findings are weighted correctly.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from harness.matcher import ExpectedFinding, MatchResult
from src.schema import Dimension, Finding

SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3}
DIMENSIONS = [d.value for d in Dimension]


def _safe_div(num: float, den: float) -> Optional[float]:
    return None if den == 0 else num / den


def score_case(
    result: MatchResult,
    findings: List[Finding],
    expected: List[ExpectedFinding],
) -> Dict:
    matched_expected = [exp for exp, _ in result.matched]

    total_expected = len(expected)
    matched = len(matched_expected)
    weighted_total = sum(SEVERITY_WEIGHT.get(e.severity, 1) for e in expected)
    weighted_matched = sum(SEVERITY_WEIGHT.get(e.severity, 1) for e in matched_expected)
    total_findings = len(findings)
    unmatched = len(result.unmatched_findings)
    snf_hits = len(result.false_positive_lines)

    by_dimension: Dict[str, Dict] = {}
    for dim in DIMENSIONS:
        exp_d = [e for e in expected if e.dimension == dim]
        match_d = [e for e in matched_expected if e.dimension == dim]
        find_d = [f for f in findings if f.dimension.value == dim]
        unmatched_d = [f for f in result.unmatched_findings if f.dimension.value == dim]
        by_dimension[dim] = {
            "total_expected": len(exp_d),
            "matched": len(match_d),
            "total_findings": len(find_d),
            "unmatched_findings": len(unmatched_d),
            "detection_rate": _safe_div(len(match_d), len(exp_d)),
            "false_positive_signal": _safe_div(len(unmatched_d), len(find_d)),
        }

    return {
        "total_expected": total_expected,
        "matched": matched,
        "weighted_total": weighted_total,
        "weighted_matched": weighted_matched,
        "total_findings": total_findings,
        "unmatched_findings": unmatched,
        "should_not_flag_hits": snf_hits,
        "detection_rate": _safe_div(matched, total_expected),
        "severity_weighted_recall": _safe_div(weighted_matched, weighted_total),
        "false_positive_signal": _safe_div(unmatched, total_findings),
        "by_dimension": by_dimension,
    }


def aggregate(case_scores: List[Dict]) -> Dict:
    """Sum raw counts across cases, then compute overall and per-dimension rates."""
    keys = [
        "total_expected",
        "matched",
        "weighted_total",
        "weighted_matched",
        "total_findings",
        "unmatched_findings",
        "should_not_flag_hits",
    ]
    totals = {k: sum(cs[k] for cs in case_scores) for k in keys}

    by_dimension: Dict[str, Dict] = {}
    for dim in DIMENSIONS:
        te = sum(cs["by_dimension"][dim]["total_expected"] for cs in case_scores)
        ma = sum(cs["by_dimension"][dim]["matched"] for cs in case_scores)
        tf = sum(cs["by_dimension"][dim]["total_findings"] for cs in case_scores)
        uf = sum(cs["by_dimension"][dim]["unmatched_findings"] for cs in case_scores)
        by_dimension[dim] = {
            "total_expected": te,
            "matched": ma,
            "total_findings": tf,
            "unmatched_findings": uf,
            "detection_rate": _safe_div(ma, te),
            "false_positive_signal": _safe_div(uf, tf),
        }

    return {
        **totals,
        "detection_rate": _safe_div(totals["matched"], totals["total_expected"]),
        "severity_weighted_recall": _safe_div(
            totals["weighted_matched"], totals["weighted_total"]
        ),
        "false_positive_signal": _safe_div(
            totals["unmatched_findings"], totals["total_findings"]
        ),
        "by_dimension": by_dimension,
    }
