import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
share_requests_table = dynamodb.Table('ShareRequests')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')

def lambda_handler(event, context):
    try:
        # Parse request
        unit_id = event['pathParameters']['unit_id']
        body = json.loads(event['body'])
        requester_email = body['requester_email']
        message = body.get('message', '')

        # Check if unit exists and is rented
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

        if unit.get('status') != 'rented':
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Unit is not currently rented"
                })
            }

        # Find who rents this unit
        rentals_response = rentals_table.scan(
            FilterExpression='unit_id = :unit_id AND #status = :active',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':unit_id': unit_id,
                ':active': 'active'
            }
        )

        if not rentals_response.get('Items'):
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "No active rental found for this unit"
                })
            }

        owner_user_id = rentals_response['Items'][0]['user_id']

        # Create share request
        request_id = str(uuid.uuid4())
        share_requests_table.put_item(
            Item={
                'request_id': request_id,
                'unit_id': unit_id,
                'requester_email': requester_email,
                'owner_user_id': owner_user_id,
                'message': message,
                'status': 'pending',
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
                "message": "Access request sent successfully",
                "request_id": request_id
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
                "error": "Failed to create access request",
                "message": str(e)
            })
        }
