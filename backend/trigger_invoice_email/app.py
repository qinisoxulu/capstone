import json
import boto3

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
users_table = dynamodb.Table('Users')

def lambda_handler(event, context):
    """
    This function is triggered by DynamoDB Streams when a new invoice is created.
    It sends invoice notification emails to users.
    """
    try:
        for record in event['Records']:
            if record['eventName'] == 'INSERT':
                # Parse the new invoice
                new_image = record['dynamodb']['NewImage']

                invoice_id = new_image.get('invoice_id', {}).get('S', 'unknown')
                user_id = new_image.get('user_id', {}).get('S', 'unknown')
                amount = new_image.get('amount', {}).get('N', '0')
                due_date = new_image.get('due_date', {}).get('S', 'unknown')
                billing_period = new_image.get('billing_period', {}).get('S', 'unknown')

                # Get user's email
                user_response = users_table.get_item(Key={'user_id': user_id})

                if 'Item' in user_response:
                    user_email = user_response['Item']['email']

                    # Send invoice email
                    try:
                        ses.send_email(
                            Source='billing@yourdomain.com',  # Replace with verified SES email
                            Destination={
                                'ToAddresses': [user_email]
                            },
                            Message={
                                'Subject': {
                                    'Data': f'Your Storage Unit Invoice - {billing_period}',
                                    'Charset': 'UTF-8'
                                },
                                'Body': {
                                    'Text': {
                                        'Data': f'Invoice Notification\n\n'
                                               f'A new invoice has been generated for your storage unit rental.\n\n'
                                               f'Invoice ID: {invoice_id}\n'
                                               f'Billing Period: {billing_period}\n'
                                               f'Amount Due: ${amount}\n'
                                               f'Due Date: {due_date}\n\n'
                                               f'Please log in to your account to view and pay your invoice.\n\n'
                                               f'Best regards,\nBilling Department',
                                        'Charset': 'UTF-8'
                                    },
                                    'Html': {
                                        'Data': f'<html><body>'
                                               f'<h2>Invoice Notification</h2>'
                                               f'<p>A new invoice has been generated for your storage unit rental.</p>'
                                               f'<table style="border-collapse: collapse; width: 100%; max-width: 500px;">'
                                               f'<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Invoice ID:</strong></td>'
                                               f'<td style="padding: 8px; border: 1px solid #ddd;">{invoice_id}</td></tr>'
                                               f'<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Billing Period:</strong></td>'
                                               f'<td style="padding: 8px; border: 1px solid #ddd;">{billing_period}</td></tr>'
                                               f'<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Amount Due:</strong></td>'
                                               f'<td style="padding: 8px; border: 1px solid #ddd;">${amount}</td></tr>'
                                               f'<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Due Date:</strong></td>'
                                               f'<td style="padding: 8px; border: 1px solid #ddd;">{due_date}</td></tr>'
                                               f'</table>'
                                               f'<p>Please log in to your account to view and pay your invoice.</p>'
                                               f'<p>Best regards,<br/>Billing Department</p>'
                                               f'</body></html>',
                                        'Charset': 'UTF-8'
                                    }
                                }
                            }
                        )
                        print(f"Invoice email sent to {user_email} for invoice {invoice_id}")
                    except Exception as email_error:
                        print(f"Failed to send invoice email: {str(email_error)}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Processed invoice events"})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
