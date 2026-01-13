import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
payment_methods_table = dynamodb.Table('PaymentMethods')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = body['user_id']
        card_last_four = body['card_last_four']
        card_type = body.get('card_type', 'credit')
        card_brand = body.get('card_brand', '')
        expiry_month = body.get('expiry_month', '')
        expiry_year = body.get('expiry_year', '')
        is_default = body.get('is_default', False)

        # Generate payment_method_id if not provided (for new cards)
        payment_method_id = body.get('payment_method_id', str(uuid.uuid4()))

        # If setting as default, unset other defaults for this user
        if is_default:
            # Scan for user's payment methods and update them
            response = payment_methods_table.scan(
                FilterExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
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

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Payment method saved successfully",
                "payment_method_id": payment_method_id
            })
        }

    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": f"Missing required field: {str(e)}"
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
                "error": "Failed to save payment method",
                "message": str(e)
            })
        }
