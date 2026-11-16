import os
from typing import List, Optional
from langchain_groq import ChatGroq

from app.core.config import settings

_key_idx = 0


def get_groq_keys() -> List[str]:
    raw = os.getenv("GROQ_API_KEYS", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys and settings.groq_api_key:
        keys = [settings.groq_api_key]
    return keys


def get_llm(temperature: float = 0.2, key_index: Optional[int] = None) -> ChatGroq:
    """
    Returns a ChatGroq client cycling through available Groq API keys to distribute quota.
    """
    global _key_idx
    keys = get_groq_keys()
    if key_index is not None:
        selected_key = keys[key_index % len(keys)]
    else:
        selected_key = keys[_key_idx % len(keys)]
        _key_idx = (_key_idx + 1) % len(keys)

    return ChatGroq(
        model=settings.groq_model,
        groq_api_key=selected_key,
        temperature=temperature,
        max_retries=3,
    )
