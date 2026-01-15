"""
Request Unit Access - Allow users to request access to a rented unit.
Sends email notification to the unit owner.
"""

import json
import os
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, error_response, not_found_error, validation_error, server_error

dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')

share_requests_table = dynamodb.Table('ShareRequests')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')
users_table = dynamodb.Table('Users')

SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@qinisoxulu.com')


def send_access_request_email(owner_email, requester_email, unit_name, message):
    """Send email notification to unit owner about access request."""
    try:
        subject = f"Access Request for Your Storage Unit - {unit_name}"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>New Access Request</h2>
            <p>Someone has requested access to your storage unit.</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Unit:</strong> {unit_name}</p>
                <p><strong>Requester:</strong> {requester_email}</p>
                {f'<p><strong>Message:</strong> {message}</p>' if message else ''}
            </div>
            <p>Log in to your <a href="https://capstone.qinisoxulu.com/dashboard.html">Capstone Dashboard</a> to approve or deny this request.</p>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated message from Capstone Storage.
            </p>
        </body>
        </html>
        """

        body_text = f"""
New Access Request

Someone has requested access to your storage unit.

Unit: {unit_name}
Requester: {requester_email}
{f'Message: {message}' if message else ''}

Log in to your Capstone Dashboard to approve or deny this request.
        """

        ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [owner_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            }
        )
        print(f"Access request email sent to {owner_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False


@require_auth
def lambda_handler(event, context):
    try:
        user_id = event['user_context']['user_id']
        user_email = event['user_context'].get('email', '')
        unit_id = event['pathParameters']['unit_id']

        body = json.loads(event['body']) if event.get('body') else {}
        message = body.get('message', '')

        # Check if unit exists
        unit_response = units_table.get_item(Key={'unit_id': unit_id})

        if 'Item' not in unit_response:
            return not_found_error("Unit")

        unit = unit_response['Item']
        unit_name = unit.get('name') or unit.get('unit_number') or unit_id

        if unit.get('status') != 'rented':
            return error_response("Invalid request", "Unit is not currently rented", 400)

        # Find who rents this unit
        rentals_response = rentals_table.query(
            IndexName='unit-index',
            KeyConditionExpression=Key('unit_id').eq(unit_id)
        )

        active_rental = None
        for rental in rentals_response.get('Items', []):
            if rental.get('status') == 'active':
                active_rental = rental
                break

        if not active_rental:
            return not_found_error("Active rental")

        owner_user_id = active_rental['user_id']

        # Get owner's email from Users table
        owner_response = users_table.get_item(Key={'user_id': owner_user_id})
        owner_email = None
        if 'Item' in owner_response:
            owner_email = owner_response['Item'].get('email')

        # Create share request
        request_id = str(uuid.uuid4())
        share_requests_table.put_item(
            Item={
                'request_id': request_id,
                'unit_id': unit_id,
                'requester_user_id': user_id,
                'requester_email': user_email,
                'owner_user_id': owner_user_id,
                'message': message,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
        )

        # Send email notification to owner
        if owner_email:
            send_access_request_email(owner_email, user_email, unit_name, message)

        return success_response({
            "message": "Access request sent successfully",
            "request_id": request_id
        }, 201)

    except KeyError as e:
        return validation_error(f"Missing required field: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return server_error()
