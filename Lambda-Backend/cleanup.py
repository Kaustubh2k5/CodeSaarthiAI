import json
import boto3
import requests
from requests_aws4auth import AWS4Auth
import time
import os

region = "ap-south-1"
service = "aoss"
host = os.environ.get("AOSS_HOST")

session = boto3.Session()
credentials = session.get_credentials().get_frozen_credentials()

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("codesaathi-sessions")


def lambda_handler(event, context):

    now = int(time.time())

    response = table.scan()
    items = response.get("Items", [])

    deleted_indexes = []

    for item in items:
        expires_at = item.get("expiresAt")
        index_name = item.get("indexName")

        if expires_at and expires_at < now and index_name:
            # Delete OpenSearch index
            url = f"https://{host}/{index_name}"
            response = requests.delete(url, auth=awsauth)

            if response.status_code in [200, 404]:
                deleted_indexes.append(index_name)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "deletedIndexes": deleted_indexes
        })
    }
