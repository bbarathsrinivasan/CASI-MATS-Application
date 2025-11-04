from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Type, get_origin

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from .safety import ensure_safe_text, have_openai


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # Placeholder; replace with GPT-5 when available


def responses_client() -> Optional[Any]:
    if not have_openai():
        return None
    return OpenAI()


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
def call_structured(
    system_prompt: str,
    user_prompt: str,
    schema_model: Type[BaseModel],
    model: str = DEFAULT_MODEL,
) -> BaseModel:
    """Call the OpenAI Responses API with a JSON schema and return a parsed Pydantic model.

    Falls back to a minimal offline mock if OPENAI_API_KEY is not set.
    """
    # Safety checks
    ensure_safe_text(system_prompt, context="system")
    ensure_safe_text(user_prompt, context="user")

    client = responses_client()
    if client is None:
        # Offline mock: populate minimal fields safely using typing inspection
        data = {}
        for name, field in schema_model.model_fields.items():
            ann = field.annotation
            origin = get_origin(ann)
            if ann is str:
                data[name] = f"mock {name}"
            elif origin is list:
                data[name] = []
            elif origin is dict:
                data[name] = {}
            elif ann in (int, float):
                data[name] = 0
            elif ann is bool:
                data[name] = False
            else:
                data[name] = None
        return schema_model.model_validate(data)

    schema_payload = {
        "name": schema_model.__name__,
        "schema": schema_model.model_json_schema(),
        "strict": True,
    }

    # Attempt Chat Completions with JSON Schema response format first
    try:
        chat = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": schema_payload,
            },
            temperature=0.2,
        )
        out_text = chat.choices[0].message.content or "{}"
    except TypeError:
        # SDK may not support json_schema response_format yet. Instruct strict JSON only.
        json_instr = (
            "Return ONLY a JSON object that strictly matches this JSON Schema. "
            "Do not include any extra text.\nSCHEMA:\n" + json.dumps(schema_payload["schema"])  # type: ignore
        )
        chat = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt + "\n" + json_instr},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        out_text = chat.choices[0].message.content or "{}"
    except Exception:
        # Final fallback to Responses API without response_format
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + "\nReturn only JSON."},
            ],
        )
        try:
            out_text = response.output_text  # type: ignore[attr-defined]
        except Exception:
            out_text = json.dumps(getattr(response, "output", {}))

    ensure_safe_text(out_text, context="model_output")

    try:
        obj = json.loads(out_text)
    except Exception:
        obj = {}
    try:
        return schema_model.model_validate(obj)
    except Exception:
        # As a final fallback, return a safe mock conforming to the schema
        data = {}
        for name, field in schema_model.model_fields.items():
            ann = field.annotation
            origin = get_origin(ann)
            if ann is str:
                data[name] = f"mock {name}"
            elif origin is list:
                data[name] = []
            elif origin is dict:
                data[name] = {}
            elif ann in (int, float):
                data[name] = 0
            elif ann is bool:
                data[name] = False
            else:
                data[name] = None
        return schema_model.model_validate(data)
