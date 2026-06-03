"""Offline self-test of the deterministic harness core (no API key required).

Proves matcher + scoring behave correctly by simulating two reviewers against the real
labeled dataset:

- a PERFECT reviewer that emits exactly the ground-truth findings  -> recall 100%, FP 0
- a NOISY reviewer that also flags a should_not_flag line          -> false_positive_signal > 0

This is the "harness-first" backbone validated without spending a single token.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from harness.matcher import ExpectedFinding, match
from harness.scoring import aggregate, score_case
from src.schema import Dimension, Finding, Severity

CASES = Path(__file__).resolve().parent.parent / "harness" / "cases" / "eval_cases.yaml"


def _finding_from_expected(e: ExpectedFinding) -> Finding:
    return Finding(
        dimension=Dimension(e.dimension),
        severity=Severity(e.severity),
        lines=e.lines,
        issue=f"simulated: {e.tag}",
        suggestion="fix it",
        tag=e.tag,
    )


def main() -> None:
    cases = yaml.safe_load(CASES.read_text(encoding="utf-8"))["cases"]

    perfect_scores = []
    noisy_scores = []
    for case in cases:
        expected = [ExpectedFinding.from_dict(e) for e in (case.get("expected_findings") or [])]
        snf = case.get("should_not_flag") or []

        # PERFECT reviewer: emits exactly the expected findings.
        perfect = [_finding_from_expected(e) for e in expected]
        pm = match(perfect, expected, should_not_flag=snf)
        perfect_scores.append(score_case(pm, perfect, expected))

        # NOISY reviewer: same, plus a bogus finding on a should_not_flag line.
        noisy = list(perfect)
        if snf:
            noisy.append(
                Finding(
                    dimension=Dimension.readability,
                    severity=Severity.low,
                    lines=[snf[0]],
                    issue="bogus",
                    suggestion="n/a",
                    tag="naming",
                )
            )
        nm = match(noisy, expected, should_not_flag=snf)
        noisy_scores.append(score_case(nm, noisy, expected))

    perfect_agg = aggregate(perfect_scores)
    noisy_agg = aggregate(noisy_scores)

    print("PERFECT reviewer  -> detection_rate:", perfect_agg["detection_rate"],
          "| false_positive_signal:", perfect_agg["false_positive_signal"])
    print("NOISY   reviewer  -> detection_rate:", noisy_agg["detection_rate"],
          "| false_positive_signal:", noisy_agg["false_positive_signal"],
          "| snf hits:", noisy_agg["should_not_flag_hits"])

    assert perfect_agg["detection_rate"] == 1.0, "perfect reviewer should catch everything"
    assert perfect_agg["false_positive_signal"] == 0.0, "perfect reviewer has no false positives"
    assert noisy_agg["false_positive_signal"] > 0.0, "noisy reviewer should show FP signal"
    assert noisy_agg["should_not_flag_hits"] > 0, "noisy reviewer trips the should_not_flag trap"
    assert perfect_agg["severity_weighted_recall"] == 1.0
    print("\nHarness core self-test: OK  (matcher + scoring are correct, deterministically)")


if __name__ == "__main__":
    main()
