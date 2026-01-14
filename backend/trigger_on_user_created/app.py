"""
Cognito Post-Confirmation Trigger - Store new user in DynamoDB and send welcome email.
Triggered automatically when a user completes signup.
"""

import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

users_table = dynamodb.Table('Users')


def lambda_handler(event, context):
    """
    Process Cognito post-confirmation trigger.

    Args:
        event: Cognito trigger event containing user attributes
        context: Lambda context

    Returns:
        event: Must return the event to Cognito
    """
    try:
        # Extract user attributes from Cognito event
        user = event["request"]["userAttributes"]
        user_id = user["sub"]
        email = user["email"]

        # Get custom attributes (set by frontend during signup)
        user_type = user.get("custom:user_type", "client")  # Default to client
        full_name = user.get("custom:full_name", "")

        # Store user in DynamoDB with all attributes
        users_table.put_item(
            Item={
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "user_type": user_type,
                "status": "active",
                "subscription_status": "trial",
                "subscription_tier": "basic",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )

        print(f"User created in DynamoDB: {user_id} ({email}) - Type: {user_type}")

        # Send welcome email via SES
        sender = os.environ.get('SENDER_EMAIL', 'noreply@qinisoxulu.com')

        try:
            ses.send_email(
                Source=sender,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': 'Welcome to Self-Storage Platform!'},
                    'Body': {
                        'Text': {
                            'Data': f'Hello {full_name or "there"},\n\nWelcome to our self-storage platform! Your account has been created successfully.\n\nYou can now browse facilities and book storage units.\n\nBest regards,\nThe Storage Team'
                        },
                        'Html': {
                            'Data': f'''
                                <h2>Welcome to Self-Storage Platform!</h2>
                                <p>Hello {full_name or "there"},</p>
                                <p>Your account has been created successfully.</p>
                                <p>You can now browse facilities and book storage units.</p>
                                <p>Best regards,<br>The Storage Team</p>
                            '''
                        }
                    }
                }
            )
            print(f"Welcome email sent to {email}")
        except Exception as email_error:
            # Log but don't fail user creation if email fails
            print(f"Failed to send welcome email: {str(email_error)}")

    except Exception as e:
        print(f"Error in post-confirmation trigger: {str(e)}")
        # Still return event to allow user signup to complete

    # MUST return event to Cognito
    return event
