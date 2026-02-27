# graph/vector_store.py

import os
from dotenv import load_dotenv
load_dotenv()
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


class VectorStore:

    def __init__(self):

        region = os.getenv("AWS_REGION", "asia-south-1")
        host = os.getenv("VECTOR_ENDPOINT")

        credentials = boto3.Session().get_credentials()

        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "aoss",
            session_token=credentials.token,
        )

        self.client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

    def save_embedding(self, symbol):

        self.client.index(
            index="symbols",
            body={
                "symbol_id": symbol.id,
                "name": symbol.name,
                "type": symbol.type,
                "description": symbol.embedding_text,
                "embedding": symbol.embedding,
            },
        )