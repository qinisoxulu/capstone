import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Facilities')

def lambda_handler(event, context):
    try:
        # Get optional city filter from query parameters
        city = None
        if event.get('queryStringParameters') and event['queryStringParameters'].get('city'):
            city = event['queryStringParameters']['city']

        # Query DynamoDB
        if city:
            # Scan with filter for city
            response = table.scan(
                FilterExpression=Attr('city').eq(city)
            )
        else:
            # Get all facilities
            response = table.scan()

        facilities = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "facilities": facilities
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
                "error": "Failed to retrieve facilities",
                "message": str(e)
            })
        }
