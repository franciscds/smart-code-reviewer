"""Data contracts for the Smart Code Reviewer.

These Pydantic models are the single source of truth. The reviewer emits a validated
``ReviewResult``; both the Streamlit UI and the eval harness consume the same shape.
The ``tag`` field on ``Finding`` is what the harness matches against ground truth, so it
must come from the controlled vocabulary (see ``harness/cases/eval_cases.yaml``).
"""
from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Dimension(str, Enum):
    readability = "readability"
    structure = "structure"
    maintainability = "maintainability"


# Weight used by severity_weighted_recall in harness/scoring.py.
SEVERITY_WEIGHT = {Severity.low: 1, Severity.medium: 2, Severity.high: 3}


class Finding(BaseModel):
    """A single issue the reviewer raises about the code."""

    dimension: Dimension
    severity: Severity
    lines: List[int] = Field(
        default_factory=list,
        description="1-based line numbers the finding refers to.",
    )
    issue: str = Field(description="What is wrong, stated plainly.")
    suggestion: str = Field(description="A concrete fix.")
    tag: str = Field(
        description="Controlled-vocabulary slug used by the harness to match ground truth."
    )


class DimensionScore(BaseModel):
    """A 0-10 score for one dimension with a short rationale."""

    dimension: Dimension
    score: int = Field(ge=0, le=10)
    rationale: str


class ReviewResult(BaseModel):
    """The full, validated output of a review."""

    summary: str
    findings: List[Finding] = Field(default_factory=list)
    scores: List[DimensionScore] = Field(default_factory=list)
    positive_note: str


if __name__ == "__main__":
    # Tiny self-check: build a minimal valid object and round-trip it through JSON.
    demo = ReviewResult(
        summary="demo",
        findings=[
            Finding(
                dimension=Dimension.readability,
                severity=Severity.low,
                lines=[1],
                issue="x",
                suggestion="y",
                tag="naming",
            )
        ],
        scores=[
            DimensionScore(dimension=Dimension.readability, score=7, rationale="ok"),
        ],
        positive_note="clear function boundaries",
    )
    print(demo.model_dump_json(indent=2))
    print("schema OK")
