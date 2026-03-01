import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("codesaathi-sessions")

def lambda_handler(event, context):
    try:
        # Handle API Gateway body
        if "body" in event and event["body"]:
            body = json.loads(event["body"])
            session_id = body.get("sessionId")
        else:
            session_id = event.get("sessionId")

        if not session_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing sessionId"})
            }

        response = table.get_item(
            Key={"sessionId": session_id}
        )

        if "Item" not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Session not found"})
            }

        item = response["Item"]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "sessionId": item.get("sessionId"),
                "status": item.get("status"),
                "indexName": item.get("indexName"),
                "repoUrl": item.get("repoUrl")
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
