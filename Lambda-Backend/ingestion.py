# ingest.py (PROTOTYPE VERSION - STABLE)

import json
import os
import boto3
import requests
from requests_aws4auth import AWS4Auth
import zipfile
import io
import time

# ===== CONFIG =====
region = "ap-south-1"
service = "aoss"
host = os.environ.get("AOSS_HOST")

ttl_seconds = 60 * 60 * 6  # 6 hours
MAX_FILE_SIZE = 300 * 1024  # 300KB limit (prototype safety)

ALLOWED_EXTENSIONS = (
    ".py", ".js", ".ts", ".java",
    ".html", ".css", ".md", ".json"
)

# ===== AWS CLIENTS =====
session = boto3.Session()
credentials = session.get_credentials().get_frozen_credentials()

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

bedrock = boto3.client("bedrock-runtime", region_name=region)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("codesaathi-sessions")


# ===== CHUNKING =====
def chunk_code(content, size=1000):
    return [content[i:i+size] for i in range(0, len(content), size)]


# ===== EMBEDDING =====
def get_embedding(text):
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": text})
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


# ===== CREATE INDEX =====
def create_index(index_name):
    url = f"https://{host}/{index_name}"

    payload = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "vector": {"type": "knn_vector", "dimension": 1024},
                "content": {"type": "text"},
                "file_path": {"type": "keyword"}
            }
        }
    }

    response = requests.put(url, auth=awsauth, json=payload)

    if response.status_code not in [200, 201]:
        if "already_exists" not in response.text:
            raise Exception(f"Index creation failed: {response.text}")


# ===== INDEX DOCUMENT =====
def index_chunk(index_name, vector, content, file_path):
    url = f"https://{host}/{index_name}/_doc"

    document = {
        "vector": vector,
        "content": content,
        "file_path": file_path
    }

    response = requests.post(url, auth=awsauth, json=document)

    if response.status_code not in [200, 201]:
        raise Exception(f"Indexing failed: {response.text}")


# ===== LAMBDA HANDLER =====
def lambda_handler(event, context):

    try:
        session_id = event["sessionId"]
        repo_url = event["repoUrl"]
        index_name = f"codesaathi-{session_id}"

        print("Starting ingestion:", session_id)

        # Mark session as PROCESSING
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":val": "PROCESSING"}
        )

        create_index(index_name)

        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]

        # Fetch repo metadata
        api_url = repo_url.replace(
            "https://github.com/",
            "https://api.github.com/repos/"
        )

        headers = {"User-Agent": "codesaathi"}
        repo_meta = requests.get(api_url, headers=headers, timeout=10)

        if repo_meta.status_code != 200:
            raise Exception(f"GitHub metadata error: {repo_meta.text}")

        default_branch = repo_meta.json().get("default_branch", "main")

        # Download ZIP
        zip_url = f"{repo_url}/archive/refs/heads/{default_branch}.zip"
        response = requests.get(zip_url, headers=headers, timeout=30)

        if response.status_code != 200:
            raise Exception(f"ZIP download failed: {response.text}")

        graph_nodes = {}
        graph_edges = []

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:

            for file_info in z.infolist():

                if file_info.is_dir():
                    continue

                if file_info.file_size > MAX_FILE_SIZE:
                    continue

                raw_path = file_info.filename
                parts = raw_path.split("/")
                path = "/".join(parts[1:]) if len(parts) > 1 else parts[0]

                # Build Graph
                parent = None
                current_path = ""

                for part in path.split("/"):
                    current_path = current_path + "/" + part if current_path else part

                    if current_path not in graph_nodes:
                        graph_nodes[current_path] = {
                            "id": current_path,
                            "label": part,
                            "type": "folder" if "." not in part else "file"
                        }

                    if parent:
                        graph_edges.append({
                            "source": parent,
                            "target": current_path
                        })

                    parent = current_path

                # Only index allowed extensions
                if not path.endswith(ALLOWED_EXTENSIONS):
                    continue

                try:
                    with z.open(file_info) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                except Exception:
                    continue

                chunks = chunk_code(content)

                for chunk in chunks:
                    embedding = get_embedding(chunk)
                    index_chunk(index_name, embedding, chunk, path)

        # Set TTL expiration
        expires_at = int(time.time()) + ttl_seconds

        # Mark READY
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="""
                SET #s = :val,
                    indexName = :idx,
                    expiresAt = :ttl,
                    graph = :graph
            """,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":val": "READY",
                ":idx": index_name,
                ":ttl": expires_at,
                ":graph": {
                    "nodes": list(graph_nodes.values()),
                    "edges": graph_edges
                }
            }
        )

        print("Ingestion complete:", session_id)

        return {"status": "success"}

    except Exception as e:
        print("INGESTION FAILED:", str(e))

        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":val": "FAILED"}
        )

        raise e