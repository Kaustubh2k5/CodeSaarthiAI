import asyncio
import json
import re

from app.llm.loader import llm
from app.llm.prompts import build_context
from app.model.llm_output import DescriptionOutput
from app.utils.cache import cache
from app.config import settings


# -------------------------
# JSON SAFETY EXTRACTION
# -------------------------

def extract_json(text: str) -> dict:
    """
    DeepSeek sometimes adds extra text.
    Extract first JSON object safely.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")

    return json.loads(match.group(0))


# -------------------------
# MAIN DESCRIBER
# -------------------------

async def describe_symbol(symbol):

    # =====================
    # 1️⃣ CACHE CHECK
    # =====================
    cache_key = cache.compute_key(symbol)

    if settings.CACHE_ENABLED:
        cached = cache.get(cache_key)
        if cached:
            symbol.description = cached["description"]
            symbol.framework_tags = cached["tags"]
            return symbol

    # =====================
    # 2️⃣ BUILD PROMPT
    # =====================
    context = build_context(symbol)

    prompt = f"""
You analyze software architecture.

Return ONLY valid JSON.
No markdown.
No explanations.

Format:
{{
  "description": "concise architectural description (max 25 words)",
  "tags": ["framework_or_role_tags"]
}}

{context}
"""

    # =====================
    # 3️⃣ CALL LLM (NON-BLOCKING)
    # =====================
    # llm.generate is sync → run in thread pool
    response = await asyncio.to_thread(
        llm.generate,
        prompt
    )

    # =====================
    # 4️⃣ SAFE JSON PARSE
    # =====================
    raw_data = extract_json(response)

    # =====================
    # 5️⃣ VALIDATE OUTPUT
    # =====================
    output = DescriptionOutput(**raw_data)

    # =====================
    # 6️⃣ APPLY RESULT
    # =====================
    symbol.description = output.description
    symbol.framework_tags = output.tags

    # =====================
    # 7️⃣ CACHE STORE
    # =====================
    if settings.CACHE_ENABLED:
        cache.set(cache_key, {
            "description": output.description,
            "tags": output.tags
        })

    return symbol