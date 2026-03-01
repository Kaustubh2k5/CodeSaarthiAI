import json
import uuid
import time
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("codesaathi-sessions")

def lambda_handler(event, context):

    body = json.loads(event["body"]) if "body" in event else event
    repo_url = body.get("repoUrl")

    if not repo_url:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "repoUrl required"})
        }

    session_id = str(uuid.uuid4())
    now = int(time.time())

    table.put_item(
        Item={
            "sessionId": session_id,
            "repoUrl": repo_url,
            "status": "CREATED",
            "createdAt": now,
            "expiresAt": now + 3600
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "sessionId": session_id,
            "status": "CREATED"
        })
    }