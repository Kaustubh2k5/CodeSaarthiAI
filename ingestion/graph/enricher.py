# graph/enricher.py

from dotenv import load_dotenv
load_dotenv()

import boto3
import json
import os
from .schemas import EnrichmentResult

# --------------------------------------------------
# BEDROCK CLIENT (Nova only now)
# --------------------------------------------------

BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=BEDROCK_REGION,
)

ENRICH_MODEL = os.getenv(
    "ENRICH_MODEL",
    "amazon.nova-lite-v1:0"
)

# --------------------------------------------------
# MODEL CALL (NOVA)
# --------------------------------------------------

def _call_model(prompt: str):

    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 500,
            "temperature": 0,
            "topP": 0.9,
        },
    }

    response = bedrock.invoke_model(
        modelId=ENRICH_MODEL,
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["results"][0]["outputText"]


# --------------------------------------------------
# MAIN ENRICHMENT
# --------------------------------------------------

def enrich_symbol(symbol):

    if symbol.type not in ("function", "class", "file"):
        return symbol

    prompt = f"""
You are a software architecture analyzer.

Return ONLY valid JSON.

JSON schema:
{{
  "responsibility": "one sentence responsibility",
  "keywords": ["technical tags"],
  "technical_summary": "concise technical explanation"
}}

Component:
Name: {symbol.name}
Type: {symbol.type}
File: {symbol.file}
Framework signals: {symbol.framework_tags}
"""

    try:
        raw = _call_model(prompt)

        start = raw.find("{")
        end = raw.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON returned")

        json_text = raw[start:end + 1]

        parsed = EnrichmentResult.model_validate_json(json_text)

    except Exception:
        parsed = EnrichmentResult(
            responsibility=f"{symbol.name} implementation",
            keywords=[],
            technical_summary="",
        )

    # ---------------- GRAPH DESCRIPTION ----------------
    symbol.description = parsed.responsibility
    symbol.keywords = parsed.keywords

    # ---------------- KB DOCUMENT CONTENT ----------------
    # This is what KB will embed automatically
    symbol.embedding_text = (
        f"Component: {symbol.name}\n"
        f"Type: {symbol.type}\n"
        f"Responsibility: {parsed.responsibility}\n"
        f"Details: {parsed.technical_summary}"
    )

    return symbol