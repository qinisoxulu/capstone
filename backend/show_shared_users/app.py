"""
Show Shared Users - Display users with shared access to a unit.
"""

import boto3
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
shared_units_table = dynamodb.Table('SharedUnits')


@require_auth
def lambda_handler(event, context):
    try:
        unit_id = event['pathParameters']['unit_id']

        # Query SharedUnits table using GSI
        response = shared_units_table.query(
            IndexName='unit-index',
            KeyConditionExpression=Key('unit_id').eq(unit_id)
        )

        shared_users = response.get('Items', [])

        return success_response({
            "unit_id": unit_id,
            "shared_users": shared_users,
            "count": len(shared_users)
        })

    except KeyError:
        return validation_error("Missing unit_id parameter")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
