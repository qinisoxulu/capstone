"""
Share Unit Access - Allow unit renters to share access with others.
"""

import json
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, validation_error, forbidden_error, server_error

dynamodb = boto3.resource('dynamodb')
shared_units_table = dynamodb.Table('SharedUnits')
rentals_table = dynamodb.Table('Rentals')


@require_auth
def lambda_handler(event, context):
    try:
        user_id = event['user_context']['user_id']
        unit_id = event['pathParameters']['unit_id']

        body = json.loads(event['body'])
        user_email = body.get('user_email')

        if not user_email:
            return validation_error("user_email is required")

        # Verify user actually rents this unit
        rentals_response = rentals_table.query(
            IndexName='unit-index',
            KeyConditionExpression=Key('unit_id').eq(unit_id)
        )

        active_rental = None
        for rental in rentals_response.get('Items', []):
            if rental.get('user_id') == user_id and rental.get('status') == 'active':
                active_rental = rental
                break

        if not active_rental:
            return forbidden_error("You do not have permission to share this unit")

        # Add shared access
        share_id = str(uuid.uuid4())
        shared_units_table.put_item(
            Item={
                'share_id': share_id,
                'unit_id': unit_id,
                'user_email': user_email,
                'granted_by': user_id,
                'granted_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
        )

        return success_response({
            "message": f"Access granted to {user_email} for unit {unit_id}",
            "share_id": share_id
        }, 201)

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
