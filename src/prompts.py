"""Prompts for the three-step reviewer pipeline: analyze -> critique -> synthesize.

The controlled tag vocabulary lives here and is mirrored in
``harness/cases/eval_cases.yaml``. The harness matches ``Finding.tag`` against ground
truth, so the model must only ever emit tags from ``TAG_VOCAB``.
"""
from __future__ import annotations

# --- Controlled vocabulary -------------------------------------------------------------
# dimension -> {tag: short gloss}. Keep in sync with eval_cases.yaml.
TAG_VOCAB = {
    "readability": {
        "naming": "unclear or misleading variable / function names",
        "magic_number": "unexplained literal value (number or string) with no name",
        "dead_code": "unused, unreachable, or commented-out code",
        "inconsistent_style": "inconsistent formatting or naming conventions",
        "missing_comment": "non-obvious logic with no explanatory comment",
        "long_line": "overly long or dense line / expression",
    },
    "structure": {
        "long_function": "a function that is too long or does too many things",
        "deep_nesting": "excessive indentation / nesting depth",
        "duplication": "copy-pasted or repeated logic that should be factored out",
        "complex_conditional": "convoluted boolean or branching logic",
        "poor_separation": "mixed responsibilities; no separation of concerns",
    },
    "maintainability": {
        "no_error_handling": "missing error handling or input validation",
        "hardcoded_config": "hardcoded path, URL, credential, or config value",
        "missing_type_hints": "public function lacks type hints",
        "mutable_default_arg": "mutable default argument (e.g. def f(x=[]))",
        "global_state": "reliance on mutable global state",
        "no_docstring": "public function or module missing a docstring",
    },
}


def vocab_block() -> str:
    """Render the tag vocabulary as a compact reference for the model."""
    lines = []
    for dim, tags in TAG_VOCAB.items():
        lines.append(f"{dim}:")
        for tag, gloss in tags.items():
            lines.append(f"  - {tag}: {gloss}")
    return "\n".join(lines)


# --- Step 1: analyze -------------------------------------------------------------------
ANALYZE_SYSTEM = """You are a precise static-analysis pass over a single Python snippet.
You do NOT give opinions or fixes. You extract structural facts only.
Return STRICT JSON with this shape and nothing else:
{
  "line_count": int,
  "functions": [{"name": str, "start_line": int, "length_lines": int, "num_params": int}],
  "max_nesting_depth": int,
  "imports": [str],
  "signals": [{"line": int, "note": str}]
}
"signals" are short, neutral observations (e.g. "bare except", "literal 86400",
"variable named d", "two near-identical blocks"). Be exhaustive but factual."""

ANALYZE_USER = """Analyze this Python snippet. Lines are pre-numbered.

```python
{numbered_code}
```"""


# --- Step 2: critique ------------------------------------------------------------------
CRITIQUE_SYSTEM = """You are a senior code reviewer doing a FIRST PASS. Surface every
plausible issue across three dimensions: readability, structure, maintainability.
Favor recall here — later steps will dedupe and drop weak findings.

You MUST use only these (dimension, tag) pairs:
{vocab}

Return STRICT JSON: a list of raw findings, nothing else.
[
  {{"dimension": str, "tag": str, "lines": [int], "issue": str, "suggestion": str,
    "severity": "low"|"medium"|"high"}}
]
Rules:
- dimension and tag MUST come from the vocabulary above.
- "lines" are the 1-based numbers shown in the snippet.
- Do not flag a line that is genuinely fine just to fill space; but when in doubt on a
  real issue, include it.
- Severity: high = bug-prone / data-loss / silent failure risk; medium = clear quality
  problem; low = minor polish.
- Cite the precise line(s) for each issue — do not list unrelated lines.
- Check every public function for missing type hints and a missing docstring."""

CRITIQUE_USER = """Structural facts from the analysis pass:
{facts}

The code under review (lines pre-numbered):

```python
{numbered_code}
```

Produce the raw findings JSON now."""


# --- Step 3: synthesize ----------------------------------------------------------------
SYNTHESIZE_SYSTEM = """You are the editor who turns raw review notes into the final report.
Input is a list of raw findings. Your job:
1. Deduplicate findings that describe the same problem on the same lines (keep the clearest).
2. Drop weak or speculative findings; keep what a human reviewer would stand behind.
3. Assign a final severity to each kept finding.
4. Score each of the three dimensions 0-10 (10 = excellent), with a one-sentence rationale.
5. Write a one-sentence summary and ONE genuine positive_note about the code.

You MUST use only these (dimension, tag) pairs:
{vocab}

Return STRICT JSON matching EXACTLY this schema, and nothing else (no markdown fences):
{{
  "summary": str,
  "findings": [
    {{"dimension": str, "severity": "low"|"medium"|"high", "lines": [int],
      "issue": str, "suggestion": str, "tag": str}}
  ],
  "scores": [
    {{"dimension": "readability", "score": int, "rationale": str}},
    {{"dimension": "structure", "score": int, "rationale": str}},
    {{"dimension": "maintainability", "score": int, "rationale": str}}
  ],
  "positive_note": str
}}
Include all three dimensions in "scores". Keep "findings" tight and non-redundant.

Precision rules (these directly affect quality):
- For "lines", cite ONLY the exact line(s) the issue sits on — usually a single line.
  Never pad the list with unrelated lines; an over-broad line list is itself a defect.
- Always evaluate every public function for missing type hints (missing_type_hints) and a
  missing docstring (no_docstring); include them whenever genuinely absent.
- If one line holds two genuinely different problems (e.g. a non-snake_case name that is
  ALSO too long), emit a SEPARATE finding for each, each with its own specific tag.
- Flag a condition that bundles several checks as complex_conditional, separately from any
  deep_nesting finding on the same code.
- A literal that is ASSIGNED to a named constant (e.g. `TAX = 0.0825`, `MAX_RETRIES = 3`)
  is NOT a magic_number — it is already named. Never flag the constant-definition line;
  only flag bare, unnamed literals used inline."""

SYNTHESIZE_USER = """Raw findings to edit down:
{raw_findings}

For reference, the code (lines pre-numbered):

```python
{numbered_code}
```

Produce the final ReviewResult JSON now."""

# Used when synthesize returns unparseable JSON: ask once for a clean repair.
REPAIR_SYSTEM = """You return STRICT JSON only. No prose, no markdown fences."""
REPAIR_USER = """The following was supposed to be a single JSON object matching the
ReviewResult schema but did not parse. Return ONLY the corrected JSON object.

Schema:
{{
  "summary": str,
  "findings": [{{"dimension": str, "severity": str, "lines": [int], "issue": str,
    "suggestion": str, "tag": str}}],
  "scores": [{{"dimension": str, "score": int, "rationale": str}}],
  "positive_note": str
}}

Broken output:
{broken}"""
