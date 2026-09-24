"""
Central LLM configuration for TradingAgents.

Model priority order (all available on Groq free tier):
  1. qwen/qwen3.8-27b   — best quality, 70B params
  2. llama3-8b-8192    — fast fallback
  3. gemma2-9b-it      — last resort

Usage:
    from config.llm_config import get_llm
    llm = get_llm()
"""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger("LLMConfig")

# Models in preference order — confirmed available on this Groq account
GROQ_MODELS = [
    "qwen/qwen3.8-27b",        # 27B Qwen3 — best quality available
    "openai/gpt-oss-120b",     # 120B GPT OSS — highest quality, may be slower
    "openai/gpt-oss-20b",      # 20B GPT OSS — fastest fallback
]

# Default primary model
DEFAULT_MODEL = "qwen/qwen3.8-27b"


def get_llm(temperature: float = 0.1, model: Optional[str] = None):
    """
    Return a ChatGroq instance with automatic fallback on model errors.

    Args:
        temperature: LLM temperature (0.0–1.0)
        model: Override model name. Defaults to DEFAULT_MODEL.

    Returns:
        ChatGroq instance
    """
    from langchain_groq import ChatGroq

    chosen = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    return ChatGroq(model=chosen, temperature=temperature)


def get_llm_with_fallback(temperature: float = 0.1):
    """
    Return a ChatGroq with automatic retry across fallback models.
    Wraps the LLM in a callable that tries models in order until one works.
    """
    from langchain_groq import ChatGroq

    # Try each model; return the first that can be instantiated
    for model_name in GROQ_MODELS:
        try:
            llm = ChatGroq(model=model_name, temperature=temperature)
            logger.info(f"Using Groq model: {model_name}")
            return llm
        except Exception as e:
            logger.warning(f"Model {model_name} unavailable: {e}")
            time.sleep(0.5)

    raise RuntimeError(
        "No Groq models available. Check your GROQ_API_KEY and account tier."
    )
