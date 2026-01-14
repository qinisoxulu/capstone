"""
Unit Access Control - Verify if a user has access to a unit (for IoT/physical access).
"""

import json
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
shared_units_table = dynamodb.Table('SharedUnits')
access_events_table = dynamodb.Table('AccessEvents')


@require_auth
def lambda_handler(event, context):
    try:
        user_id = event['user_context']['user_id']
        user_email = event['user_context'].get('email', '')

        body = json.loads(event['body'])
        unit_id = body.get('unit_id')

        if not unit_id:
            return validation_error("unit_id is required")

        # Check if user is the renter
        is_owner = False
        rentals_response = rentals_table.query(
            IndexName='unit-index',
            KeyConditionExpression=Key('unit_id').eq(unit_id)
        )

        for rental in rentals_response.get('Items', []):
            if rental.get('user_id') == user_id and rental.get('status') == 'active':
                is_owner = True
                break

        # Check if user has shared access
        has_shared_access = False
        if user_email:
            shared_response = shared_units_table.query(
                IndexName='unit-index',
                KeyConditionExpression=Key('unit_id').eq(unit_id) & Key('user_email').eq(user_email)
            )
            for share in shared_response.get('Items', []):
                if share.get('status') == 'active':
                    has_shared_access = True
                    break

        # Determine access
        has_access = is_owner or has_shared_access
        access_type = 'owner' if is_owner else ('shared' if has_shared_access else 'denied')

        # Log access attempt
        event_id = str(uuid.uuid4())
        access_events_table.put_item(
            Item={
                'event_id': event_id,
                'unit_id': unit_id,
                'user_id': user_id,
                'user_email': user_email or 'unknown',
                'access_granted': has_access,
                'access_type': access_type,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        return success_response({
            "access_granted": has_access,
            "access_type": access_type
        })

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
