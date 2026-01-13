import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
shared_units_table = dynamodb.Table('SharedUnits')
access_events_table = dynamodb.Table('AccessEvents')

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body'])
        unit_id = body['unit_id']
        user_email = body.get('user_email')
        user_id = body.get('user_id')

        # Check if user is the renter
        is_owner = False
        if user_id:
            rentals_response = rentals_table.scan(
                FilterExpression='unit_id = :unit_id AND user_id = :user_id AND #status = :active',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':unit_id': unit_id,
                    ':user_id': user_id,
                    ':active': 'active'
                }
            )
            is_owner = len(rentals_response.get('Items', [])) > 0

        # Check if user has shared access
        has_shared_access = False
        if user_email:
            shared_response = shared_units_table.get_item(
                Key={
                    'unit_id': unit_id,
                    'user_email': user_email
                }
            )
            has_shared_access = 'Item' in shared_response and shared_response['Item'].get('status') == 'active'

        # Determine access
        has_access = is_owner or has_shared_access

        # Log access attempt
        access_events_table.put_item(
            Item={
                'event_id': f"{unit_id}_{datetime.utcnow().timestamp()}",
                'unit_id': unit_id,
                'user_id': user_id or 'unknown',
                'user_email': user_email or 'unknown',
                'access_granted': has_access,
                'access_type': 'owner' if is_owner else ('shared' if has_shared_access else 'denied'),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "access_granted": has_access,
                "access_type": 'owner' if is_owner else ('shared' if has_shared_access else 'none')
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
                "error": "Failed to verify access",
                "message": str(e)
            })
        }
