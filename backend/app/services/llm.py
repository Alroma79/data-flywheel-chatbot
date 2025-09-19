# backend/app/services/llm.py
"""
Minimal LLM service wrapper.

- In demo/fallback/no-key mode: returns a deterministic stub (no network).
- In real mode: calls OpenAI Chat Completions.
"""

from __future__ import annotations

import os
from typing import Optional

def _use_stub() -> bool:
    return (
        os.getenv("DEMO_MODE") == "1"
        or os.getenv("FORCE_FALLBACK") == "1"
        or not os.getenv("OPENAI_API_KEY")
    )

async def llm(prompt: str, model: Optional[str] = None, temperature: float = 0.2) -> str:
    """
    Async chat entrypoint used by routes: `await llm("...")`.
    Returns a plain text reply.
    """
    if _use_stub():
        # Deterministic, CI-safe reply. Trim to keep logs tidy.
        return f"[stub] {prompt[:160]}"

    # --- Real provider path (OpenAI 1.x client) ---
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model = model or os.getenv("MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        content = resp.choices[0].message.content
        return content or ""
    except Exception as e:
        # Never crash the API; surface a safe fallback.
        return f"[fallback-error: {type(e).__name__}] {prompt[:160]}"

__all__ = ["llm"]
