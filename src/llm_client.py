"""Provider-agnostic LLM wrapper.

Every model call in the system goes through ``LLMClient.complete``. Swapping Anthropic
for another provider is a one-line change inside ``_complete_anthropic`` (or a new
backend method) — nothing else in the codebase imports a vendor SDK.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values, load_dotenv

# Load the project's .env once, on import, so every entry point (smoke, harness, app)
# sees the key regardless of the current working directory.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH if _ENV_PATH.exists() else None)

DEFAULT_MODEL = "claude-sonnet-4-6"


class LLMClientError(RuntimeError):
    """Raised when the client is misconfigured (e.g. missing API key)."""


def _resolve_env(name: str, explicit: Optional[str] = None) -> Optional[str]:
    """Resolve a setting with precedence: explicit arg > non-empty env var > .env file.

    A blank/whitespace env var (e.g. an ``ANTHROPIC_API_KEY=`` exported by the shell)
    must not shadow the real value in .env, so it is treated as unset.
    """
    if explicit and explicit.strip():
        return explicit.strip()
    value = os.getenv(name)
    if value and value.strip():
        return value.strip()
    if _ENV_PATH.exists():
        file_value = dotenv_values(_ENV_PATH).get(name)
        if file_value and file_value.strip():
            return file_value.strip()
    return None


class LLMClient:
    """Thin, deterministic-by-default wrapper around a chat model."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
    ) -> None:
        self.model = _resolve_env("ANTHROPIC_MODEL", model) or DEFAULT_MODEL
        self.temperature = temperature
        self._api_key = _resolve_env("ANTHROPIC_API_KEY", api_key)
        if not self._api_key:
            raise LLMClientError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        # Imported lazily and only here: the rest of the codebase stays vendor-free.
        import anthropic

        self._client = anthropic.Anthropic(api_key=self._api_key)

    def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        """Send one (system, user) turn and return the model's text response."""
        return self._complete_anthropic(system, user, max_tokens)

    def _complete_anthropic(self, system: str, user: str, max_tokens: int) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
