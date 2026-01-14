"""
Upsert Payment Method - Add or update payment methods for authenticated users.
"""

import json
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
payment_methods_table = dynamodb.Table('PaymentMethods')


@require_auth
def lambda_handler(event, context):
    try:
        user_id = event['user_context']['user_id']

        body = json.loads(event['body'])
        card_last_four = body.get('card_last_four')
        card_type = body.get('card_type', 'credit')
        card_brand = body.get('card_brand', '')
        expiry_month = body.get('expiry_month', '')
        expiry_year = body.get('expiry_year', '')
        is_default = body.get('is_default', False)

        if not card_last_four:
            return validation_error("card_last_four is required")

        # Generate payment_method_id if not provided (for new cards)
        payment_method_id = body.get('payment_method_id', str(uuid.uuid4()))

        # If setting as default, unset other defaults for this user
        if is_default:
            response = payment_methods_table.query(
                IndexName='user-index',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )

            for item in response.get('Items', []):
                if item.get('is_default'):
                    payment_methods_table.update_item(
                        Key={'payment_method_id': item['payment_method_id']},
                        UpdateExpression='SET is_default = :false',
                        ExpressionAttributeValues={':false': False}
                    )

        # Upsert payment method
        payment_methods_table.put_item(
            Item={
                'payment_method_id': payment_method_id,
                'user_id': user_id,
                'card_last_four': card_last_four,
                'card_type': card_type,
                'card_brand': card_brand,
                'expiry_month': expiry_month,
                'expiry_year': expiry_year,
                'is_default': is_default,
                'created_at': datetime.utcnow().isoformat()
            }
        )

        return success_response({
            "message": "Payment method saved successfully",
            "payment_method_id": payment_method_id
        }, 201)

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
