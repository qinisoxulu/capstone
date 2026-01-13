import json
import boto3
from datetime import datetime
from decimal import Decimal
import uuid

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = body['user_id']
        unit_id = body['unit_id']
        payment_method_id = body.get('payment_method_id')

        # Check if unit is available
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

        if unit.get('status') != 'available':
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Unit is not available for rent"
                })
            }

        # Create rental record
        rental_id = str(uuid.uuid4())
        rental_start_date = datetime.utcnow().isoformat()

        rental_item = {
            'rental_id': rental_id,
            'user_id': user_id,
            'unit_id': unit_id,
            'facility_id': unit.get('facility_id'),
            'start_date': rental_start_date,
            'status': 'active',
            'payment_method_id': payment_method_id,
            'monthly_price': unit.get('price', Decimal('0')),
            'created_at': rental_start_date
        }

        # Use DynamoDB transaction to atomically create rental and update unit
        client = boto3.client('dynamodb')

        response = client.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': 'Rentals',
                        'Item': {
                            'rental_id': {'S': rental_id},
                            'user_id': {'S': user_id},
                            'unit_id': {'S': unit_id},
                            'facility_id': {'S': str(unit.get('facility_id', ''))},
                            'start_date': {'S': rental_start_date},
                            'status': {'S': 'active'},
                            'payment_method_id': {'S': payment_method_id or ''},
                            'monthly_price': {'N': str(unit.get('price', 0))},
                            'created_at': {'S': rental_start_date}
                        }
                    }
                },
                {
                    'Update': {
                        'TableName': 'Units',
                        'Key': {'unit_id': {'S': unit_id}},
                        'UpdateExpression': 'SET #status = :rented, rented_by = :user_id',
                        'ExpressionAttributeNames': {
                            '#status': 'status'
                        },
                        'ExpressionAttributeValues': {
                            ':rented': {'S': 'rented'},
                            ':user_id': {'S': user_id}
                        }
                    }
                }
            ]
        )

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Rental created successfully",
                "rental_id": rental_id,
                "rental": rental_item
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
                "error": "Failed to create rental",
                "message": str(e)
            })
        }
