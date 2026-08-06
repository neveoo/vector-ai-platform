"""
Small abstraction over "call an LLM and get text back" so the rest of
the app (classification.py, rag.py) doesn't care which provider is
behind it. Swapping providers later -- e.g. once there's budget for
Anthropic's API, or to compare providers for the eval writeup -- is a
one-line config change (LLM_PROVIDER in .env), not a rewrite.

Currently supports:
- "gemini": Google's free tier (no credit card, no expiration) -- the
  default, since this project is being built without a paid API budget.
- "anthropic": paid, higher quality, useful to A/B against Gemini for
  docs/EVALS.md once budget allows.
"""
from app.core.config import get_settings

settings = get_settings()


def call_llm(prompt: str, max_tokens: int = 1000) -> str:
    if settings.llm_provider == "gemini":
        return _call_gemini(prompt, max_tokens)
    elif settings.llm_provider == "anthropic":
        return _call_anthropic(prompt, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


def _call_gemini(prompt: str, max_tokens: int) -> str:
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,  # e.g. "gemini-2.5-flash" -- free tier model
        contents=prompt,
        config={"max_output_tokens": max_tokens},
    )
    return response.text


def _call_anthropic(prompt: str, max_tokens: int) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.chat_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
