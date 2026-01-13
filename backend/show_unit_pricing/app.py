import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')

def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Get unit_id from path parameters
        unit_id = event['pathParameters']['unit_id']

        # Get unit details
        unit_response = units_table.get_item(Key={'unit_id': unit_id})

        if 'Item' not in unit_response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Unit not found"
                })
            }

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
            "currency": "USD"
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(pricing_info, default=decimal_to_float)
        }

    except KeyError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Missing unit_id parameter"
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Failed to retrieve unit pricing",
                "message": str(e)
            })
        }
