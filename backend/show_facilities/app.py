"""
Show Facilities - Public endpoint to list all storage facilities.
"""

import boto3
from boto3.dynamodb.conditions import Attr

from response_utils import success_response, server_error

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
            response = table.scan(FilterExpression=Attr('city').eq(city))
        else:
            response = table.scan()

        facilities = response.get('Items', [])

        return success_response({"facilities": facilities})

    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
