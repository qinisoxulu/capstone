import json
import boto3
from datetime import datetime
from decimal import Decimal
import uuid

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
invoices_table = dynamodb.Table('Invoices')

def lambda_handler(event, context):
    """
    This function is triggered by EventBridge on a schedule (e.g., monthly).
    It creates invoices for all active rentals.
    """
    try:
        # Get all active rentals
        response = rentals_table.scan(
            FilterExpression='#status = :active',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':active': 'active'}
        )

        rentals = response.get('Items', [])
        invoices_created = 0

        for rental in rentals:
            try:
                # Create invoice
                invoice_id = str(uuid.uuid4())
                current_date = datetime.utcnow().isoformat()

                invoice = {
                    'invoice_id': invoice_id,
                    'user_id': rental['user_id'],
                    'rental_id': rental['rental_id'],
                    'unit_id': rental['unit_id'],
                    'facility_id': rental.get('facility_id'),
                    'amount': rental.get('monthly_price', Decimal('0')),
                    'status': 'pending',
                    'due_date': current_date,
                    'created_at': current_date,
                    'billing_period': datetime.utcnow().strftime('%Y-%m')
                }

                invoices_table.put_item(Item=invoice)
                invoices_created += 1

                print(f"Invoice {invoice_id} created for rental {rental['rental_id']}")

            except Exception as rental_error:
                print(f"Error creating invoice for rental {rental.get('rental_id')}: {str(rental_error)}")
                continue

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Billing cycle completed. {invoices_created} invoices created.",
                "invoices_created": invoices_created
            })
        }

    except Exception as e:
        print(f"Error in recurring billing: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Failed to process recurring billing",
                "message": str(e)
            })
        }
