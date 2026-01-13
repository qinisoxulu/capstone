import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
invoices_table = dynamodb.Table('Invoices')

def lambda_handler(event, context):
    try:
        # Get user_id from query parameters
        user_id = event['queryStringParameters']['user_id']

        # Query Invoices table for this user
        response = invoices_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )

        invoices = response.get('Items', [])

        # Sort by date descending (most recent first)
        invoices.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "invoices": invoices,
                "count": len(invoices)
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
                "error": "Failed to retrieve invoices",
                "message": str(e)
            })
        }
