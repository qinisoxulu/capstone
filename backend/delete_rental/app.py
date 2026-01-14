"""
Delete Rental - Allow authenticated users to cancel their storage unit rentals.
"""

import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Import from Lambda layer
from auth_utils import require_auth
from response_utils import success_response, error_response, not_found_error, forbidden_error, server_error

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')


@require_auth
def lambda_handler(event, context):
    """
    Delete/cancel a rental for the authenticated user.

    Path Parameters:
        - rental_id: ID of the rental to delete

    Returns:
        API response with success message or error
    """
    try:
        # Extract authenticated user from Cognito claims
        user_id = event['user_context']['user_id']

        # Get rental_id from path parameters
        rental_id = event['pathParameters'].get('rental_id')

        if not rental_id:
            return error_response("Missing rental_id", "rental_id path parameter is required", 400)

        # Get rental details
        rental_response = rentals_table.get_item(Key={'rental_id': rental_id})

        if 'Item' not in rental_response:
            return not_found_error("Rental")

        rental = rental_response['Item']

        # Verify ownership
        if rental['user_id'] != user_id:
            return forbidden_error("You can only delete your own rentals")

        # Get the unit_id to release
        unit_id = rental.get('unit_id')

        # Use transaction to atomically update rental status and release unit
        dynamodb_client = boto3.client('dynamodb')
        now = datetime.utcnow().isoformat()

        transact_items = [
            {
                'Update': {
                    'TableName': 'Rentals',
                    'Key': {'rental_id': {'S': rental_id}},
                    'UpdateExpression': 'SET #status = :cancelled, cancelled_at = :now',
                    'ExpressionAttributeNames': {'#status': 'status'},
                    'ExpressionAttributeValues': {
                        ':cancelled': {'S': 'cancelled'},
                        ':now': {'S': now},
                        ':active': {'S': 'active'}
                    },
                    'ConditionExpression': '#status = :active'
                }
            }
        ]

        # Release the unit if it exists
        if unit_id:
            transact_items.append({
                'Update': {
                    'TableName': 'Units',
                    'Key': {'unit_id': {'S': unit_id}},
                    'UpdateExpression': 'SET #status = :available REMOVE rented_by',
                    'ExpressionAttributeNames': {'#status': 'status'},
                    'ExpressionAttributeValues': {
                        ':available': {'S': 'available'}
                    }
                }
            })

        dynamodb_client.transact_write_items(TransactItems=transact_items)

        print(f"Rental cancelled: {rental_id} - User: {user_id}, Unit: {unit_id}")

        return success_response({
            "message": "Rental cancelled successfully",
            "rental_id": rental_id
        })

    except dynamodb_client.exceptions.TransactionCanceledException as e:
        return error_response("Cannot cancel rental", "Rental is not active or already cancelled", 400)
    except Exception as e:
        print(f"Error deleting rental: {str(e)}")
        return server_error()
