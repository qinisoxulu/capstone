import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')

def lambda_handler(event, context):
    try:
        # Get facility_id from path parameters
        facility_id = event['pathParameters']['facility_id']

        # Query Units table for this facility
        response = units_table.scan(
            FilterExpression=Attr('facility_id').eq(facility_id) & Attr('status').eq('available')
        )

        units = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "facility_id": facility_id,
                "available_units": units,
                "count": len(units)
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
                "error": "Missing facility_id parameter"
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
                "error": "Failed to retrieve facility availability",
                "message": str(e)
            })
        }
