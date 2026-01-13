import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
share_requests_table = dynamodb.Table('ShareRequests')
shared_units_table = dynamodb.Table('SharedUnits')

def lambda_handler(event, context):
    try:
        # Parse request
        request_id = event['pathParameters']['request_id']
        body = json.loads(event['body'])
        action = body['action']  # 'approve' or 'deny'

        # Get share request details
        request_response = share_requests_table.get_item(Key={'request_id': request_id})

        if 'Item' not in request_response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Share request not found"
                })
            }

        share_request = request_response['Item']

        if share_request.get('status') != 'pending':
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Request has already been processed"
                })
            }

        # Update share request status
        if action == 'approve':
            # Update request status
            share_requests_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression='SET #status = :approved, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':approved': 'approved',
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )

            # Add to SharedUnits
            shared_units_table.put_item(
                Item={
                    'unit_id': share_request['unit_id'],
                    'user_email': share_request['requester_email'],
                    'granted_by': share_request['owner_user_id'],
                    'granted_at': datetime.utcnow().isoformat(),
                    'status': 'active'
                }
            )

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "message": "Access request approved"
                })
            }

        elif action == 'deny':
            # Update request status
            share_requests_table.update_item(
                Key={'request_id': request_id},
                UpdateExpression='SET #status = :denied, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':denied': 'denied',
                    ':updated_at': datetime.utcnow().isoformat()
                }
            )

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "message": "Access request denied"
                })
            }

        else:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Invalid action. Must be 'approve' or 'deny'"
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
                "error": "Failed to process share request",
                "message": str(e)
            })
        }
