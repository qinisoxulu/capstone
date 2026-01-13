import json
import boto3

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
rentals_table = dynamodb.Table('Rentals')
users_table = dynamodb.Table('Users')

def lambda_handler(event, context):
    """
    This function is triggered by DynamoDB Streams when an access event occurs.
    It sends security notifications for unauthorized access attempts.
    """
    try:
        for record in event['Records']:
            if record['eventName'] == 'INSERT':
                # Parse the new access event
                new_image = record['dynamodb']['NewImage']

                # Check if access was denied
                access_granted = new_image.get('access_granted', {}).get('BOOL', True)

                if not access_granted:
                    # Unauthorized access attempt - send notification
                    unit_id = new_image.get('unit_id', {}).get('S', 'unknown')
                    user_email = new_image.get('user_email', {}).get('S', 'unknown')
                    timestamp = new_image.get('timestamp', {}).get('S', 'unknown')

                    # Find the owner of the unit
                    rentals_response = rentals_table.scan(
                        FilterExpression='unit_id = :unit_id AND #status = :active',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':unit_id': unit_id,
                            ':active': 'active'
                        }
                    )

                    if rentals_response.get('Items'):
                        owner_user_id = rentals_response['Items'][0]['user_id']

                        # Get owner's email
                        user_response = users_table.get_item(Key={'user_id': owner_user_id})

                        if 'Item' in user_response:
                            owner_email = user_response['Item']['email']

                            # Send security alert
                            try:
                                ses.send_email(
                                    Source='security@yourdomain.com',  # Replace with verified SES email
                                    Destination={
                                        'ToAddresses': [owner_email]
                                    },
                                    Message={
                                        'Subject': {
                                            'Data': 'Security Alert: Unauthorized Access Attempt',
                                            'Charset': 'UTF-8'
                                        },
                                        'Body': {
                                            'Text': {
                                                'Data': f'Security Alert\n\n'
                                                       f'An unauthorized access attempt was detected for your storage unit.\n\n'
                                                       f'Unit ID: {unit_id}\n'
                                                       f'Attempted by: {user_email}\n'
                                                       f'Time: {timestamp}\n\n'
                                                       f'If this was you, please contact support.\n\n'
                                                       f'Best regards,\nSecurity Team',
                                                'Charset': 'UTF-8'
                                            },
                                            'Html': {
                                                'Data': f'<html><body>'
                                                       f'<h2 style="color: red;">Security Alert</h2>'
                                                       f'<p>An unauthorized access attempt was detected for your storage unit.</p>'
                                                       f'<ul>'
                                                       f'<li><strong>Unit ID:</strong> {unit_id}</li>'
                                                       f'<li><strong>Attempted by:</strong> {user_email}</li>'
                                                       f'<li><strong>Time:</strong> {timestamp}</li>'
                                                       f'</ul>'
                                                       f'<p>If this was you, please contact support.</p>'
                                                       f'<p>Best regards,<br/>Security Team</p>'
                                                       f'</body></html>',
                                                'Charset': 'UTF-8'
                                            }
                                        }
                                    }
                                )
                                print(f"Security alert sent to {owner_email}")
                            except Exception as email_error:
                                print(f"Failed to send security alert: {str(email_error)}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Processed access events"})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
