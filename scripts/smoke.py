"""Phase 1 acceptance: round-trip one prompt through LLMClient and print the response."""
from __future__ import annotations

from src.llm_client import LLMClient


def main() -> None:
    client = LLMClient()
    print(f"model: {client.model}")
    reply = client.complete(
        system="You are a terse assistant. Answer in one short sentence.",
        user="In one sentence, what makes code easy to maintain?",
        max_tokens=100,
    )
    print("response:", reply.strip())


if __name__ == "__main__":
    main()
