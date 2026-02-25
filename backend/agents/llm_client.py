"""
Shared LLM Client — supports Groq (primary), OpenAI, and local fallback.

Priority:
  1. Groq  (LLM_PROVIDER=groq)   — ultra-fast Llama 3.3 70B
  2. OpenAI (LLM_PROVIDER=openai) — GPT-4o-mini
  3. Local  (USE_LOCAL_LLM=true)  — template-based fallback

Usage:
    from backend.agents.llm_client import call_llm
    text = call_llm(system="...", user="...", max_tokens=600)
    # Returns str on success, None to trigger template fallback
"""
import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)


def _call_groq(system: str, user: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call Groq API using the openai-compatible client."""
    key = settings.GROQ_API_KEY
    if not key or not key.startswith("gsk_"):
        logger.warning("Groq API key missing or malformed.")
        return None
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model=settings.LLM_MODEL or "llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content.strip()
        logger.info(
            f"[Groq] Call succeeded — model={settings.LLM_MODEL}, "
            f"tokens={response.usage.total_tokens}"
        )
        return text
    except Exception as e:
        logger.error(f"[Groq] Call failed: {e}")
        return None


def _call_openai(system: str, user: str, max_tokens: int, temperature: float) -> Optional[str]:
    """Call OpenAI API."""
    key = settings.OPENAI_API_KEY
    if not key or not key.startswith("sk-"):
        logger.warning("OpenAI API key missing or malformed.")
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content.strip()
        logger.info(
            f"[OpenAI] Call succeeded — model={settings.LLM_MODEL}, "
            f"tokens={response.usage.total_tokens}"
        )
        return text
    except Exception as e:
        logger.error(f"[OpenAI] Call failed: {e}")
        return None


def call_llm(
    system: str,
    user: str,
    max_tokens: int = 800,
    temperature: float = 0.3,
) -> Optional[str]:
    """
    Call the configured LLM provider.
    Returns response text, or None if unavailable (triggers template fallback).

    Provider priority:
      groq → openai → None (template fallback)
    """
    # Local / disabled
    if settings.USE_LOCAL_LLM:
        return None

    provider = (settings.LLM_PROVIDER or "local").lower()

    if provider == "groq":
        result = _call_groq(system, user, max_tokens, temperature)
        if result:
            return result
        # Auto-fallback to OpenAI if Groq fails
        logger.info("[LLM] Groq failed — attempting OpenAI fallback...")
        return _call_openai(system, user, max_tokens, temperature)

    if provider == "openai":
        return _call_openai(system, user, max_tokens, temperature)

    logger.info(f"[LLM] Provider '{provider}' not recognised — using template fallback.")
    return None
