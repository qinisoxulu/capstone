"""
Show Share Requests - Retrieve share requests for authenticated user's units.
Returns pending and processed access requests.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, server_error

dynamodb = boto3.resource('dynamodb')
share_requests_table = dynamodb.Table('ShareRequests')


@require_auth
def lambda_handler(event, context):
    """
    Retrieve share requests for authenticated user's units.

    Returns:
        API response with list of share requests
    """
    try:
        user_id = event['user_context']['user_id']

        # Query share requests using owner-index GSI
        response = share_requests_table.query(
            IndexName='owner-index',
            KeyConditionExpression=Key('owner_user_id').eq(user_id)
        )

        requests = response.get('Items', [])

        # Sort by created_at descending (most recent first)
        requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        print(f"Retrieved {len(requests)} share requests for user {user_id}")

        return success_response({
            "share_requests": requests,
            "count": len(requests)
        })

    except Exception as e:
        print(f"Error retrieving share requests: {str(e)}")
        return server_error()
