import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
import zipfile
import io
import time
from tree_sitter_languages import get_parser
import os

# ===== CONFIG =====
region = "ap-south-1"
service = "aoss"
host = os.environ.get("AOSS_HOST")

ttl_seconds = 60 * 60 * 6  # 6 hours

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
# ===== TREE-SITTER SEMANTIC CHUNKING =====


# ---------------- LANGUAGE MAP ----------------
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sh": "bash"
}

FILENAME_LANGUAGE_MAP = {
    "Dockerfile": "dockerfile",
    "Makefile": "make"
}

# parser cache (VERY IMPORTANT for Lambda performance)
PARSERS = {}


def detect_language(file_path):
    filename = os.path.basename(file_path)

    if filename in FILENAME_LANGUAGE_MAP:
        return FILENAME_LANGUAGE_MAP[filename]

    ext = os.path.splitext(filename)[1].lower()
    return LANGUAGE_MAP.get(ext)


def get_ts_parser(file_path):
    lang = detect_language(file_path)
    if not lang:
        return None

    if lang not in PARSERS:
        PARSERS[lang] = get_parser(lang)

    return PARSERS[lang]

def extract_symbol_name(node, content_bytes):
    for child in node.children:
        if child.type == "identifier":
            return content_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="ignore")
    return ""

# ===== CHUNKING =====
def chunk_code(content, file_path):
    """
    DROP-IN replacement for naive chunking.
    Returns semantic code chunks using Tree-sitter.
    """

    parser = get_ts_parser(file_path)

    # fallback if unsupported language
    if parser is None:
        return [{
            "content": content,
            "symbol_type": "file",
            "symbol_name": os.path.basename(file_path)
        }]

    content_bytes = bytes(content, "utf8")
    tree = parser.parse(content_bytes)
    root = tree.root_node

    chunks = []

    TARGET_NODE_TYPES = {
        "function_definition",
        "function_declaration",
        "method_definition",
        "class_definition",
        "class_declaration",
        "lexical_declaration",
        "export_statement"
    }

    def walk(node):

        if node.type in TARGET_NODE_TYPES:
            snippet = content_bytes[node.start_byte:node.end_byte].decode(
                "utf-8", errors="ignore"
            )

            symbol_name = extract_symbol_name(node, content_bytes)

            chunks.append({
                "content": snippet,
                "symbol_type": node.type,
                "symbol_name": symbol_name
            })

        for child in node.children:
            walk(child)

    walk(root)

    # fallback if nothing detected
    if not chunks:
        chunks.append({
            "content": content,
            "symbol_type": "file",
            "symbol_name": os.path.basename(file_path)
        })

    return chunks
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
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1024
                },
                "content": {"type": "text"},
                "file_path": {"type": "text"}
            }
        }
    }

    response = requests.put(url, auth=awsauth, json=payload)

    if response.status_code not in [200, 201]:
        if "already_exists" not in response.text:
            print("Index creation error:", response.status_code, response.text)


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
        print("Indexing failed:", response.status_code, response.text)


# ===== WORKER =====
def lambda_handler(event, context):

    try:
        session_id = event["sessionId"]
        repo_url = event["repoUrl"]

        index_name = f"codesaathi-{session_id}"

        # Mark session as PROCESSING
        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":val": "PROCESSING"}
        )

        create_index(index_name)

        if repo_url.endswith(".git"):
            repo_url = repo_url.replace(".git", "")

        # Get default branch dynamically
        api_url = repo_url.replace("https://github.com/", "https://api.github.com/repos/")

        repo_meta = requests.get(api_url)

        if repo_meta.status_code != 200:
            raise Exception("Invalid GitHub repository")

        default_branch = repo_meta.json().get("default_branch", "main")

        zip_url = f"{repo_url}/archive/refs/heads/{default_branch}.zip"

        response = requests.get(zip_url)

        if response.status_code != 200:
            raise Exception("Failed to download repository")

        if response.status_code != 200:
            raise Exception("Failed to download repository")

        graph_nodes = {}
        graph_edges = []

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:

            for file_info in z.infolist():

                if file_info.is_dir():
                    continue

                # Build Graph
                path = file_info.filename
                parts = path.split("/")

                parent = None
                current_path = ""

                for part in parts:
                    if not part:
                        continue

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

                # Only index code files
                if not path.endswith((".py", ".js", ".ts", ".java")):
                    continue

                with z.open(file_info) as f:
                    content = f.read().decode("utf-8", errors="ignore")

                chunks = chunk_code(content, path)

                for chunk in chunks:
                    embedding = get_embedding(chunk["content"])

                    index_chunk(
                        index_name,
                        embedding,
                        chunk["content"],
                        path,
                        chunk["symbol_type"],
                        chunk["symbol_name"]
                    )

        # Set TTL expiration
        expires_at = int(time.time()) + ttl_seconds

        # Mark READY and store graph
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

    except Exception as e:

        print("Worker failed:", str(e))

        table.update_item(
            Key={"sessionId": session_id},
            UpdateExpression="SET #s = :val",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":val": "FAILED"}
        )

        raise e