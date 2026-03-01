import json
import boto3

lambda_client = boto3.client("lambda")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("codesaathi-sessions")
print("MASTER LAMBDA HIT")
def lambda_handler(event, context):

    # Parse request
    body = json.loads(event["body"]) if "body" in event else event

    session_id = body.get("sessionId")
    repo_url = body.get("repoUrl")

    if not session_id or not repo_url:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing sessionId or repoUrl"})
        }

    # Create / update session
    table.put_item(
        Item={
            "sessionId": session_id,
            "status": "PROCESSING"
        }
    )

    # Invoke worker asynchronously
    lambda_client.invoke(
        FunctionName="codesaathi-ingest",
        InvocationType="Event",
        Payload=json.dumps({
            "sessionId": session_id,
            "repoUrl": repo_url
        })
    )

    # IMPORTANT: return sessionId to frontend
    return {
        "statusCode": 200,
        "body": json.dumps({
            "sessionId": session_id,
            "status": "PROCESSING"
        })
    }