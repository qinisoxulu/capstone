import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
shared_units_table = dynamodb.Table('SharedUnits')
rentals_table = dynamodb.Table('Rentals')

def lambda_handler(event, context):
    try:
        # Parse request
        unit_id = event['pathParameters']['unit_id']
        body = json.loads(event['body'])
        user_email = body['user_email']
        owner_user_id = body['owner_user_id']  # User granting access

        # Verify owner actually rents this unit
        rentals_response = rentals_table.scan(
            FilterExpression='unit_id = :unit_id AND user_id = :user_id AND #status = :active',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':unit_id': unit_id,
                ':user_id': owner_user_id,
                ':active': 'active'
            }
        )

        if not rentals_response.get('Items'):
            return {
                "statusCode": 403,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "You do not have permission to share this unit"
                })
            }

        # Add shared access
        shared_units_table.put_item(
            Item={
                'unit_id': unit_id,
                'user_email': user_email,
                'granted_by': owner_user_id,
                'granted_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
        )

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": f"Access granted to {user_email} for unit {unit_id}"
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
                "error": "Failed to share unit access",
                "message": str(e)
            })
        }
