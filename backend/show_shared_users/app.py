import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
shared_units_table = dynamodb.Table('SharedUnits')

def lambda_handler(event, context):
    try:
        # Get unit_id from path parameters
        unit_id = event['pathParameters']['unit_id']

        # Query SharedUnits table for this unit
        response = shared_units_table.query(
            KeyConditionExpression=Key('unit_id').eq(unit_id)
        )

        shared_users = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "unit_id": unit_id,
                "shared_users": shared_users,
                "count": len(shared_users)
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
                "error": "Failed to retrieve shared users",
                "message": str(e)
            })
        }
