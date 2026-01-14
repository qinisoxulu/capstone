"""
Show Payment Methods - Retrieve payment methods for authenticated user.
Returns default payment method first.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, server_error

dynamodb = boto3.resource('dynamodb')
payment_methods_table = dynamodb.Table('PaymentMethods')


@require_auth
def lambda_handler(event, context):
    """
    Retrieve payment methods for authenticated user.

    Returns:
        API response with list of payment methods
    """
    try:
        user_id = event['user_context']['user_id']

        # Query payment methods using user-index GSI
        response = payment_methods_table.query(
            IndexName='user-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        payment_methods = response.get('Items', [])

        # Sort by default first, then by created date
        payment_methods.sort(key=lambda x: (not x.get('is_default', False), x.get('created_at', '')))

        print(f"Retrieved {len(payment_methods)} payment methods for user {user_id}")

        return success_response({
            "payment_methods": payment_methods,
            "count": len(payment_methods)
        })

    except Exception as e:
        print(f"Error retrieving payment methods: {str(e)}")
        return server_error()
