"""
Create Rental - Allow authenticated users to book storage units.
Supports both subscription-based and one-time rentals.
"""

import json
import os
import uuid
import boto3
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

# Import from Lambda layer
from auth_utils import require_auth
from response_utils import success_response, error_response, validation_error, not_found_error, forbidden_error, server_error

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')
rentals_table = dynamodb.Table('Rentals')
payment_methods_table = dynamodb.Table('PaymentMethods')


@require_auth
def lambda_handler(event, context):
    """
    Create a new rental for the authenticated user.

    Request Body:
        - unit_id (required): ID of the unit to rent
        - payment_method_id (required): ID of the payment method to use
        - rental_type (optional): 'subscription' or 'one-time', defaults to 'subscription'

    Returns:
        API response with rental details or error
    """
    try:
        # Extract authenticated user from Cognito claims
        user_id = event['user_context']['user_id']

        # Parse request body
        body = json.loads(event['body'])
        unit_id = body.get('unit_id')
        payment_method_id = body.get('payment_method_id')
        rental_type = body.get('rental_type', 'subscription')  # Default to subscription

        # Validate required fields
        if not unit_id:
            return validation_error("unit_id is required")

        if not payment_method_id:
            return validation_error("payment_method_id is required")

        if rental_type not in ['subscription', 'one-time']:
            return validation_error("rental_type must be 'subscription' or 'one-time'")

        # Skip payment method validation for mock payments (testing/demo)
        if payment_method_id != 'mock-payment':
            # Validate payment method belongs to authenticated user
            pm_response = payment_methods_table.query(
                IndexName='user-index',
                KeyConditionExpression=Key('user_id').eq(user_id),
                FilterExpression=Attr('payment_method_id').eq(payment_method_id)
            )

            if not pm_response.get('Items'):
                return forbidden_error("Invalid payment method")

        # Get unit details and verify it's available
        unit_response = units_table.get_item(Key={'unit_id': unit_id})

        if 'Item' not in unit_response:
            return not_found_error("Unit")

        unit = unit_response['Item']

        if unit.get('status') != 'available':
            return error_response("Unit unavailable", "This unit is already rented or unavailable", 400)

        # Create rental with atomic transaction
        rental_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        rental = {
            'rental_id': rental_id,
            'user_id': user_id,
            'unit_id': unit_id,
            'facility_id': unit['facility_id'],
            'start_date': now,
            'status': 'active',
            'rental_type': rental_type,
            'payment_method_id': payment_method_id,
            'monthly_price': unit['price'],
            'created_at': now
        }

        # Use transaction to atomically create rental and update unit status
        dynamodb_client = boto3.client('dynamodb')

        # Helper function to convert Decimal to DynamoDB format
        def to_dynamodb_format(value):
            if isinstance(value, Decimal):
                return {'N': str(value)}
            return {'S': str(value)}

        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': 'Rentals',
                        'Item': {k: to_dynamodb_format(v) for k, v in rental.items()},
                        'ConditionExpression': 'attribute_not_exists(rental_id)'
                    }
                },
                {
                    'Update': {
                        'TableName': 'Units',
                        'Key': {'unit_id': {'S': unit_id}},
                        'UpdateExpression': 'SET #status = :rented, rented_by = :user_id',
                        'ExpressionAttributeNames': {'#status': 'status'},
                        'ExpressionAttributeValues': {
                            ':rented': {'S': 'rented'},
                            ':user_id': {'S': user_id},
                            ':available': {'S': 'available'}
                        },
                        'ConditionExpression': '#status = :available'
                    }
                }
            ]
        )

        print(f"Rental created: {rental_id} - User: {user_id}, Unit: {unit_id}, Type: {rental_type}")

        return success_response({
            "message": "Rental created successfully",
            "rental_id": rental_id,
            "rental": rental
        }, 201)

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error creating rental: {str(e)}")
        return server_error()
