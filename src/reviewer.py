"""The reviewer pipeline: analyze -> critique -> synthesize.

This is the ONLY module that calls the model (via ``LLMClient``). Each step has one job:

- ``analyze``    extract neutral structural facts about the snippet
- ``critique``   surface raw findings per dimension (high recall)
- ``synthesize`` dedupe, rank, score, and return a validated ``ReviewResult``
"""
from __future__ import annotations

import json
from typing import Any, List, Optional

from pydantic import ValidationError

from src import prompts
from src.llm_client import LLMClient
from src.schema import ReviewResult


def number_lines(code: str) -> str:
    """Prefix each line with its 1-based number so findings can cite lines."""
    lines = code.splitlines()
    width = len(str(len(lines))) if lines else 1
    return "\n".join(f"{i + 1:>{width}} | {line}" for i, line in enumerate(lines))


def _extract_json(text: str) -> Any:
    """Best-effort parse of JSON that may be wrapped in prose or markdown fences."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences if present.
    if text.startswith("```"):
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text.strip("`")
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the largest bracketed span.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("Could not parse JSON from model output.")


class Reviewer:
    def __init__(self, client: Optional[LLMClient] = None) -> None:
        self.client = client or LLMClient()

    # --- Step 1 ------------------------------------------------------------------------
    def analyze(self, numbered_code: str) -> str:
        """Return structural facts as a JSON string (passed verbatim into critique)."""
        out = self.client.complete(
            system=prompts.ANALYZE_SYSTEM,
            user=prompts.ANALYZE_USER.format(numbered_code=numbered_code),
        )
        # We keep it as text; critique only needs it as context, not as typed data.
        try:
            return json.dumps(_extract_json(out), indent=2)
        except ValueError:
            return out.strip()

    # --- Step 2 ------------------------------------------------------------------------
    def critique(self, numbered_code: str, facts: str) -> List[dict]:
        """Return a list of raw finding dicts (high recall, not yet deduped)."""
        out = self.client.complete(
            system=prompts.CRITIQUE_SYSTEM.format(vocab=prompts.vocab_block()),
            user=prompts.CRITIQUE_USER.format(facts=facts, numbered_code=numbered_code),
        )
        data = _extract_json(out)
        return data if isinstance(data, list) else data.get("findings", [])

    # --- Step 3 ------------------------------------------------------------------------
    def synthesize(self, numbered_code: str, raw_findings: List[dict]) -> ReviewResult:
        """Dedupe / rank / score raw findings into a validated ReviewResult.

        Retries once with a repair prompt if the first JSON fails to validate.
        """
        out = self.client.complete(
            system=prompts.SYNTHESIZE_SYSTEM.format(vocab=prompts.vocab_block()),
            user=prompts.SYNTHESIZE_USER.format(
                raw_findings=json.dumps(raw_findings, indent=2),
                numbered_code=numbered_code,
            ),
        )
        try:
            return ReviewResult.model_validate(_extract_json(out))
        except (ValueError, ValidationError):
            repaired = self.client.complete(
                system=prompts.REPAIR_SYSTEM,
                user=prompts.REPAIR_USER.format(broken=out),
            )
            return ReviewResult.model_validate(_extract_json(repaired))

    # --- Orchestration -----------------------------------------------------------------
    def review(self, code: str) -> ReviewResult:
        numbered = number_lines(code)
        facts = self.analyze(numbered)
        raw = self.critique(numbered, facts)
        return self.synthesize(numbered, raw)


def review(code: str, client: Optional[LLMClient] = None) -> ReviewResult:
    """Convenience entry point used by the UI and the harness."""
    return Reviewer(client=client).review(code)
