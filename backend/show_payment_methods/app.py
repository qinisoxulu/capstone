import json
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
payment_methods_table = dynamodb.Table('PaymentMethods')

def lambda_handler(event, context):
    try:
        # Get user_id from query parameters
        user_id = event['queryStringParameters']['user_id']

        # Query PaymentMethods table for this user
        response = payment_methods_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )

        payment_methods = response.get('Items', [])

        # Sort by default first, then by created date
        payment_methods.sort(key=lambda x: (not x.get('is_default', False), x.get('created_at', '')))

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "payment_methods": payment_methods,
                "count": len(payment_methods)
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
                "error": "Failed to retrieve payment methods",
                "message": str(e)
            })
        }
