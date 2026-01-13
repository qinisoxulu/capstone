import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')

def lambda_handler(event, context):
    try:
        # Get rental_id from path parameters
        rental_id = event['pathParameters']['rental_id']

        # Get rental details
        rental_response = rentals_table.get_item(Key={'rental_id': rental_id})

        if 'Item' not in rental_response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Rental not found"
                })
            }

        rental = rental_response['Item']
        unit_id = rental['unit_id']

        # Use DynamoDB transaction to atomically update rental and unit
        client = boto3.client('dynamodb')

        response = client.transact_write_items(
            TransactItems=[
                {
                    'Update': {
                        'TableName': 'Rentals',
                        'Key': {'rental_id': {'S': rental_id}},
                        'UpdateExpression': 'SET #status = :cancelled, end_date = :end_date',
                        'ExpressionAttributeNames': {
                            '#status': 'status'
                        },
                        'ExpressionAttributeValues': {
                            ':cancelled': {'S': 'cancelled'},
                            ':end_date': {'S': datetime.utcnow().isoformat()}
                        }
                    }
                },
                {
                    'Update': {
                        'TableName': 'Units',
                        'Key': {'unit_id': {'S': unit_id}},
                        'UpdateExpression': 'SET #status = :available REMOVE rented_by',
                        'ExpressionAttributeNames': {
                            '#status': 'status'
                        },
                        'ExpressionAttributeValues': {
                            ':available': {'S': 'available'}
                        }
                    }
                }
            ]
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Rental cancelled successfully",
                "rental_id": rental_id
            })
        }

    except KeyError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Missing rental_id parameter"
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
                "error": "Failed to cancel rental",
                "message": str(e)
            })
        }
