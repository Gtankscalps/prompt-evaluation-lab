"""Thin LLM client.

Uses the OpenAI API when OPENAI_API_KEY is set. Without a key, the rest
of the project falls back to the recorded sample outputs in
sample_outputs.json so the full pipeline (extraction -> scoring ->
report) can still be run and inspected offline.
"""

import os


def llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def complete(prompt: str) -> str:
    """Send one prompt to the model and return the raw text response."""
    from openai import OpenAI  # imported lazily; only needed in live mode

    client = OpenAI()
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""
