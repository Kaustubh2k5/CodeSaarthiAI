import json
import boto3
import math
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import os
# ===== CONFIG =====
region = "ap-south-1"
MAX_CONTEXT_CHARS = 12000
MAX_RESULTS = 8
MIN_SCORE = 0.2

INFERENCE_PROFILE_ARN = os.environ.get("INFERENCE_PROFILE_ARN")

# ===== AWS =====
bedrock = boto3.client("bedrock-runtime", region_name=region)
dynamodb = boto3.resource("dynamodb")

sessions_table = dynamodb.Table("codesaathi-sessions")
vectors_table = dynamodb.Table("codesaathi-vectors")


# =========================
# HELPERS
# =========================

def decimal_to_float(obj):
    if isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def cosine_similarity(v1, v2):
    dot = sum(a*b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a*a for a in v1))
    norm2 = math.sqrt(sum(b*b for b in v2))

    if norm1 == 0 or norm2 == 0:
        return 0

    return dot / (norm1 * norm2)


def get_embedding(text):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text})
    )
    return json.loads(response["body"].read())["embedding"]


# =========================
# VECTOR SEARCH (PAGINATED)
# =========================

def vector_search(session_id, query_vector):

    items = []
    last_key = None

    while True:
        if last_key:
            response = vectors_table.query(
                KeyConditionExpression=Key("sessionId").eq(session_id),
                ExclusiveStartKey=last_key
            )
        else:
            response = vectors_table.query(
                KeyConditionExpression=Key("sessionId").eq(session_id)
            )

        items.extend(response.get("Items", []))

        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break

    scored = []

    for item in items:

        embedding = decimal_to_float(item["embedding"])

        score = cosine_similarity(query_vector, embedding)

        if score >= MIN_SCORE:
            scored.append({
                "score": score,
                "content": item["content"],
                "file_path": item["filePath"]
            })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:MAX_RESULTS]


# =========================
# CLAUDE
# =========================

def ask_claude(context, question):

    prompt = f"""
You are CodeSaathi AI.

Answer ONLY using provided snippets.
If not found say:
"The answer is not present in the indexed code."

CODE SNIPPETS:
{context}

QUESTION:
{question}
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 600,
        "temperature": 0,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = bedrock.invoke_model(
        modelId=INFERENCE_PROFILE_ARN,
        body=json.dumps(body)
    )

    result = json.loads(response["body"].read())

    return result["content"][0]["text"]


# =========================
# LAMBDA HANDLER
# =========================

def lambda_handler(event, context):

    try:

        body = json.loads(event["body"]) if "body" in event else event

        session_id = body.get("sessionId")
        question = body.get("question")

        if not session_id or not question:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Missing sessionId or question"})
            }

        session = sessions_table.get_item(Key={"sessionId": session_id})

        if "Item" not in session:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Session not found"})
            }

        if session["Item"].get("status") != "READY":
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Repository not ready"})
            }

        query_vector = get_embedding(question)

        hits = vector_search(session_id, query_vector)

        if not hits:
            return {
                "statusCode": 200,
                "headers": cors_headers(),
                "body": json.dumps({
                    "answer": "No relevant code found."
                })
            }

        context_parts = []
        total_chars = 0

        for h in hits:
            snippet = f"File: {h['file_path']}\n{h['content']}\n"
            if total_chars + len(snippet) > MAX_CONTEXT_CHARS:
                break

            context_parts.append(snippet)
            total_chars += len(snippet)

        answer = ask_claude("\n\n".join(context_parts), question)

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "answer": answer,
                "sources": [h["file_path"] for h in hits]
            })
        }

    except Exception as e:

        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({
                "error": str(e)
            })
        }


# =========================
# CORS
# =========================

def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST"
    }