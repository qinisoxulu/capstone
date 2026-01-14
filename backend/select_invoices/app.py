"""
Select Invoices - Retrieve invoices for authenticated user.
Supports filtering by status.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

from auth_utils import require_auth
from response_utils import success_response, server_error

dynamodb = boto3.resource('dynamodb')
invoices_table = dynamodb.Table('Invoices')


@require_auth
def lambda_handler(event, context):
    """
    Retrieve invoices for authenticated user.

    Query params:
        - status (optional): Filter by invoice status (pending, paid, failed)

    Returns:
        API response with list of invoices
    """
    try:
        user_id = event['user_context']['user_id']

        # Get optional status filter
        query_params = event.get('queryStringParameters') or {}
        status_filter = query_params.get('status')

        # Query invoices using user-index GSI
        if status_filter:
            response = invoices_table.query(
                IndexName='user-index',
                KeyConditionExpression=Key('user_id').eq(user_id),
                FilterExpression=Attr('status').eq(status_filter)
            )
        else:
            response = invoices_table.query(
                IndexName='user-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )

        invoices = response.get('Items', [])

        # Sort by created_at descending (most recent first)
        invoices.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        print(f"Retrieved {len(invoices)} invoices for user {user_id}")

        return success_response({
            "invoices": invoices,
            "count": len(invoices)
        })

    except Exception as e:
        print(f"Error retrieving invoices: {str(e)}")
        return server_error()
