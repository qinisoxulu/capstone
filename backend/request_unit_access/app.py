"""
Request Unit Access - Allow users to request access to a rented unit.
"""

import json
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, error_response, not_found_error, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
share_requests_table = dynamodb.Table('ShareRequests')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')


@require_auth
def lambda_handler(event, context):
    try:
        user_id = event['user_context']['user_id']
        user_email = event['user_context'].get('email', '')
        unit_id = event['pathParameters']['unit_id']

        body = json.loads(event['body']) if event.get('body') else {}
        message = body.get('message', '')

        # Check if unit exists
        unit_response = units_table.get_item(Key={'unit_id': unit_id})

        if 'Item' not in unit_response:
            return not_found_error("Unit")

        unit = unit_response['Item']

        if unit.get('status') != 'rented':
            return error_response("Invalid request", "Unit is not currently rented", 400)

        # Find who rents this unit
        rentals_response = rentals_table.query(
            IndexName='unit-index',
            KeyConditionExpression=Key('unit_id').eq(unit_id)
        )

        active_rental = None
        for rental in rentals_response.get('Items', []):
            if rental.get('status') == 'active':
                active_rental = rental
                break

        if not active_rental:
            return not_found_error("Active rental")

        owner_user_id = active_rental['user_id']

        # Create share request
        request_id = str(uuid.uuid4())
        share_requests_table.put_item(
            Item={
                'request_id': request_id,
                'unit_id': unit_id,
                'requester_user_id': user_id,
                'requester_email': user_email,
                'owner_user_id': owner_user_id,
                'message': message,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
        )

        return success_response({
            "message": "Access request sent successfully",
            "request_id": request_id
        }, 201)

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
