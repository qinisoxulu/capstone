import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
share_requests_table = dynamodb.Table('ShareRequests')

def lambda_handler(event, context):
    try:
        # Get user_id from query parameters
        user_id = event['queryStringParameters']['user_id']

        # Query ShareRequests table for requests to this user's units
        response = share_requests_table.scan(
            FilterExpression=Attr('owner_user_id').eq(user_id)
        )

        requests = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "share_requests": requests,
                "count": len(requests)
            })
        }

    except KeyError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Missing user_id parameter"
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Failed to retrieve share requests",
                "message": str(e)
            })
        }
