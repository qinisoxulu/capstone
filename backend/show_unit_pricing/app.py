"""
Show Unit Pricing - Public endpoint to view pricing for a specific unit.
"""

import boto3
from decimal import Decimal

from response_utils import success_response, not_found_error, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')


def lambda_handler(event, context):
    try:
        unit_id = event['pathParameters']['unit_id']

        unit_response = units_table.get_item(Key={'unit_id': unit_id})

        if 'Item' not in unit_response:
            return not_found_error("Unit")

        unit = unit_response['Item']
        base_price = unit.get('price', Decimal('0'))

        # Calculate pricing with potential discounts
        discount_percent = unit.get('discount_percent', Decimal('0'))
        discount_amount = base_price * (discount_percent / Decimal('100'))
        final_price = base_price - discount_amount

        pricing_info = {
            "unit_id": unit_id,
            "base_price": base_price,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "final_price": final_price,
            "currency": "ZAR"
        }

        return success_response(pricing_info)

    except KeyError:
        return validation_error("Missing unit_id parameter")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
