import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')

def lambda_handler(event, context):
    try:
        # Get unit_id from path parameters
        unit_id = event['pathParameters']['unit_id']

        # Get unit details from DynamoDB
        response = units_table.get_item(
            Key={'unit_id': unit_id}
        )

        if 'Item' not in response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Unit not found"
                })
            }

        unit = response['Item']

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "unit": unit
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
                "error": "Missing unit_id parameter"
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
                "error": "Failed to retrieve unit details",
                "message": str(e)
            })
        }
