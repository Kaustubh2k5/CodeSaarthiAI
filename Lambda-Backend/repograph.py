import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("codesaathi-sessions")

def lambda_handler(event, context):

    if "body" in event:
        body = json.loads(event["body"])
    else:
        body = event

    session_id = body.get("sessionId")

    if not session_id:
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Missing sessionId"})
        }

    response = table.get_item(Key={"sessionId": session_id})

    if "Item" not in response:
        return {
            "statusCode": 404,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Session not found"})
        }

    graph = response["Item"].get("graph", {
        "nodes": [],
        "edges": []
    })

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST"
        },
        "body": json.dumps(graph)
    }