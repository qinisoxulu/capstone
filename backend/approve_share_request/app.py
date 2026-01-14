"""
Approve Share Request - Unit owner approves or denies access requests from others.
Requires authentication and ownership verification (CRITICAL SECURITY).
"""

import json
import uuid
import boto3
from datetime import datetime

from auth_utils import require_auth
from response_utils import success_response, error_response, validation_error, not_found_error, forbidden_error, server_error

dynamodb = boto3.resource('dynamodb')
share_requests_table = dynamodb.Table('ShareRequests')
shared_units_table = dynamodb.Table('SharedUnits')


@require_auth
def lambda_handler(event, context):
    """
    Process share request approval or denial.

    Path params:
        - request_id: ID of the share request

    Request body:
        - action: 'approve' or 'deny'

    Returns:
        Success or error message
    """
    try:
        user_id = event['user_context']['user_id']
        request_id = event['pathParameters']['request_id']
        body = json.loads(event['body'])
        action = body.get('action')

        # Validate action
        if action not in ['approve', 'deny']:
            return validation_error("action must be 'approve' or 'deny'")

        # Get share request
        request_response = share_requests_table.get_item(Key={'request_id': request_id})

        if 'Item' not in request_response:
            return not_found_error("Share request")

        share_request = request_response['Item']

        # CRITICAL: Verify ownership - only the unit owner can approve/deny
        if share_request['owner_user_id'] != user_id:
            return forbidden_error("You can only process your own share requests")

        if share_request.get('status') != 'pending':
            return error_response("Request already processed", "This request has already been approved or denied", 400)

        # Process the request
        if action == 'approve':
            # Generate unique share_id
            share_id = str(uuid.uuid4())

            # Update request status
            share_requests_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression='SET #status = :approved, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':approved': 'approved',
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )

            # Add to SharedUnits with share_id as primary key
            shared_units_table.put_item(
                Item={
                    'share_id': share_id,
                    'unit_id': share_request['unit_id'],
                    'user_email': share_request['requester_email'],
                    'granted_by': share_request['owner_user_id'],
                    'granted_at': datetime.utcnow().isoformat(),
                    'status': 'active'
                }
            )

            print(f"Share request {request_id} approved by {user_id}")

            return success_response({
                "message": "Access request approved",
                "share_id": share_id
            })

        else:  # action == 'deny'
            # Update request status
            share_requests_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression='SET #status = :denied, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':denied': 'denied',
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )

            print(f"Share request {request_id} denied by {user_id}")

            return success_response({
                "message": "Access request denied"
            })

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error processing share request: {str(e)}")
        return server_error()
