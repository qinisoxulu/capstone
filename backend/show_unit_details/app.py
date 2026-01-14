"""
Show Unit Details - Public endpoint to view details of a specific unit.
"""

import boto3

from response_utils import success_response, not_found_error, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')


def lambda_handler(event, context):
    try:
        unit_id = event['pathParameters']['unit_id']

        response = units_table.get_item(Key={'unit_id': unit_id})

        if 'Item' not in response:
            return not_found_error("Unit")

        return success_response({"unit": response['Item']})

    except KeyError:
        return validation_error("Missing unit_id parameter")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
