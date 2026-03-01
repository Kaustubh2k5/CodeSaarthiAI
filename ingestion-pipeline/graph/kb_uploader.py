import os
import json
import boto3


class KnowledgeBaseUploader:

    def __init__(self):

        self.bucket = os.getenv("KB_S3_BUCKET")
        self.prefix = os.getenv("KB_S3_PREFIX", "symbols/")

        self.s3 = boto3.client("s3")

    # -----------------------------------
    # Upload symbol as KB document
    # -----------------------------------
    def upload_symbol(self, symbol):

        key = f"{self.prefix}{symbol.id}.json"

        document = {
            "content": symbol.embedding_text,
            "metadata": {
                "symbol_id": symbol.id,
                "name": symbol.name,
                "type": symbol.type,
                "file": symbol.file,
                "repo_id": symbol.repo_id,
                "tenant_id": symbol.tenant_id,
                "keywords": symbol.keywords,
            },
        }

        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(document),
            ContentType="application/json",
        )