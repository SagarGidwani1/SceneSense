"""
Single entry point for structured-JSON LLM calls.
Order: each configured Gemini model (multimodal) -> Groq text model (images dropped).
Returns (parsed_json, provider_label). Raises LLMUnavailable if every provider fails,
so callers can fall back explicitly instead of silently using fake data.
"""
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger("scenesense.llm")


class LLMUnavailable(RuntimeError):
    pass


def _parse_json(text: str) -> Any:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    return json.loads(text)


def _gemini(prompt: str, images: List[Tuple[str, Path]], model: str) -> Any:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    parts: list = [prompt]
    for label, path in images:
        parts.append(label)
        parts.append(types.Part.from_bytes(data=path.read_bytes(), mime_type="image/jpeg"))
    resp = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    return _parse_json(resp.text or "")


def _groq(prompt: str) -> Any:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model=settings.groq_llm_model,
        messages=[
            {"role": "system", "content": "You are a precise analysis engine. Reply with a single JSON object only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return _parse_json(resp.choices[0].message.content or "")


def llm_json(prompt: str, images: Optional[List[Tuple[str, Path]]] = None) -> Tuple[Any, str]:
    errors = []
    if settings.gemini_api_key:
        for model in settings.gemini_models:
            for attempt in range(2):  # one retry for transient 429/503
                try:
                    return _gemini(prompt, images or [], model), f"gemini:{model}"
                except Exception as e:
                    msg = str(e)
                    errors.append(f"{model}: {msg[:160]}")
                    logger.warning("Gemini %s failed: %s", model, msg[:200])
                    if not any(c in msg for c in ("429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                        break  # permanent error (404, bad request) — next model
                    time.sleep(3)
    if settings.groq_api_key:
        try:
            note = "" if not images else "\n\n(No images available — infer visual context from transcript only.)"
            return _groq(prompt + note), f"groq:{settings.groq_llm_model}"
        except Exception as e:
            errors.append(f"groq: {str(e)[:160]}")
            logger.warning("Groq LLM failed: %s", str(e)[:200])
    raise LLMUnavailable("; ".join(errors) or "No GEMINI_API_KEY or GROQ_API_KEY configured")
