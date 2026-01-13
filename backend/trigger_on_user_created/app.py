import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
users_table = dynamodb.Table('Users')

def lambda_handler(event, context):
    try:
        # Extract user attributes from Cognito event
        user = event["request"]["userAttributes"]
        user_id = user["sub"]
        email = user["email"]

        # Store user in DynamoDB
        users_table.put_item(
            Item={
                "user_id": user_id,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
        )

        print(f"User {user_id} created successfully in DynamoDB")

        # Send welcome email via SES
        try:
            response = ses.send_email(
                Source='noreply@yourdomain.com',  # Replace with your verified SES email
                Destination={
                    'ToAddresses': [email]
                },
                Message={
                    'Subject': {
                        'Data': 'Welcome to Self-Storage Management',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': f'Hi there,\n\nWelcome to our Self-Storage Management system! '
                                   f'Your account has been successfully created.\n\n'
                                   f'You can now browse facilities, rent storage units, and manage your rentals.\n\n'
                                   f'Best regards,\nThe Self-Storage Team',
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': f'<html><body>'
                                   f'<h2>Welcome to Self-Storage Management!</h2>'
                                   f'<p>Hi there,</p>'
                                   f'<p>Your account has been successfully created.</p>'
                                   f'<p>You can now:</p>'
                                   f'<ul>'
                                   f'<li>Browse storage facilities in your area</li>'
                                   f'<li>Rent storage units</li>'
                                   f'<li>Manage your rentals and invoices</li>'
                                   f'<li>Share access with others</li>'
                                   f'</ul>'
                                   f'<p>Best regards,<br/>The Self-Storage Team</p>'
                                   f'</body></html>',
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            print(f"Welcome email sent to {email}")
        except Exception as email_error:
            print(f"Failed to send email: {str(email_error)}")
            # Don't fail the user creation if email fails

        # Return event to Cognito
        return event

    except Exception as e:
        print(f"Error: {str(e)}")
        # Still return event to allow user creation
        return event
