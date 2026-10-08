"""
Generates a grounded answer to a general electrical question, using ONLY
retrieved knowledge-base excerpts as context (spec sections 16, 59): the
model is explicitly told not to add facts beyond what it's given, and to
say so plainly when the excerpts don't cover the question.

Same optional-key philosophy as ai_service.py: if ANTHROPIC_API_KEY isn't
set, or the call fails, the caller (routes/knowledge.py) falls back to
returning the raw, cited excerpts instead of a generated paragraph - so
/knowledge/ask always returns something useful, AI or not.
"""
from typing import Optional

import httpx

from app.config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def generate_grounded_answer(query: str, excerpts: list[dict]) -> Optional[str]:
    """
    excerpts: list of {"source": document_title, "content": chunk_text}
    Returns generated answer text, or None if AI is unavailable or the call
    failed (caller falls back to showing the raw excerpts with sources).
    """
    if not settings.ANTHROPIC_API_KEY or not excerpts:
        return None

    context = "\n\n".join(f"[Source: {e['source']}]\n{e['content']}" for e in excerpts)

    system_prompt = (
        "You are an electrical-product buying and safety assistant for an "
        "Indian audience. Answer the user's question using ONLY the "
        "excerpts provided below - do not add facts, specifications, or "
        "safety advice that are not present in them. If the excerpts don't "
        "contain enough information to answer, say so plainly instead of "
        "guessing or using general knowledge. Keep the answer concise (2-4 "
        "short paragraphs or a short list), written for a non-technical "
        "homeowner. Do not recommend a specific product or brand to "
        "purchase - that happens elsewhere in the app."
    )
    user_prompt = f"Excerpts:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    try:
        response = httpx.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ANTHROPIC_MODEL,
                "max_tokens": 500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        text = "".join(block.get("text", "") for block in data.get("content", [])).strip()
        return text or None
    except Exception:
        return None
