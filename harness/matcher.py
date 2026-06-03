"""Deterministic matcher: map reviewer findings to expected (ground-truth) findings.

Default strategy (PRD): match on ``dimension`` + ``tag``, with a line-proximity tiebreak.
Each expected finding is matched to at most one reviewer finding, and vice versa
(one-to-one greedy assignment by proximity). A hook is provided for an optional
LLM-as-judge semantic matcher (stretch goal) via the ``judge`` parameter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from src.schema import Finding


@dataclass
class ExpectedFinding:
    dimension: str
    tag: str
    severity: str
    lines: List[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ExpectedFinding":
        return cls(
            dimension=str(d["dimension"]),
            tag=str(d["tag"]),
            severity=str(d.get("severity", "low")),
            lines=list(d.get("lines", []) or []),
        )


@dataclass
class MatchResult:
    matched: List[tuple]  # list of (ExpectedFinding, Finding)
    missed: List[ExpectedFinding]  # expected with no reviewer finding
    unmatched_findings: List[Finding]  # reviewer findings not tied to any expected
    false_positive_lines: List[Finding]  # findings touching a should_not_flag line


def _line_proximity(expected_lines: List[int], finding_lines: List[int]) -> float:
    """Higher is closer. 100 for any overlap, else decays with the minimum gap."""
    if not expected_lines or not finding_lines:
        return 0.5  # tag+dimension agree but no line info to compare — weak positive
    if set(expected_lines) & set(finding_lines):
        return 100.0
    gap = min(abs(a - b) for a in expected_lines for b in finding_lines)
    return 1.0 / (1.0 + gap)


def match(
    findings: List[Finding],
    expected: List[ExpectedFinding],
    should_not_flag: Optional[List[int]] = None,
    judge: Optional[Callable[[Finding, ExpectedFinding], bool]] = None,
) -> MatchResult:
    """Greedy one-to-one matching of findings to expected findings.

    ``judge`` (optional) is an LLM-as-judge hook: when provided it may rescue a pair that
    the deterministic rule rejected (same dimension, semantically the same issue).
    """
    should_not_flag = should_not_flag or []

    # Build candidate pairs that satisfy the deterministic rule (dimension + tag).
    candidates = []  # (proximity, expected_idx, finding_idx)
    for ei, exp in enumerate(expected):
        for fi, find in enumerate(findings):
            same = find.dimension.value == exp.dimension and find.tag == exp.tag
            if not same and judge is not None:
                same = find.dimension.value == exp.dimension and judge(find, exp)
            if same:
                candidates.append((_line_proximity(exp.lines, find.lines), ei, fi))

    candidates.sort(key=lambda c: c[0], reverse=True)

    used_expected: set = set()
    used_findings: set = set()
    matched: List[tuple] = []
    for _prox, ei, fi in candidates:
        if ei in used_expected or fi in used_findings:
            continue
        used_expected.add(ei)
        used_findings.add(fi)
        matched.append((expected[ei], findings[fi]))

    missed = [exp for i, exp in enumerate(expected) if i not in used_expected]
    unmatched_findings = [f for i, f in enumerate(findings) if i not in used_findings]

    snf = set(should_not_flag)
    false_positive_lines = [f for f in findings if snf & set(f.lines)]

    return MatchResult(
        matched=matched,
        missed=missed,
        unmatched_findings=unmatched_findings,
        false_positive_lines=false_positive_lines,
    )
