"""
Trigger Recurring Billing - EventBridge scheduled function.
Creates monthly invoices for active subscription-based rentals.
Runs on the 1st of each month at midnight UTC.
"""

import json
import uuid
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
invoices_table = dynamodb.Table('Invoices')


def lambda_handler(event, context):
    """
    Create invoices for all active subscription rentals.

    Returns:
        Summary of invoices created
    """
    try:
        # Get current billing period (YYYY-MM)
        now = datetime.utcnow()
        billing_period = now.strftime('%Y-%m')

        # Due date: 15th of current month
        due_date = datetime(now.year, now.month, 15).isoformat()

        # Query active rentals using GSI
        response = rentals_table.query(
            IndexName='status-index',
            KeyConditionExpression=Key('status').eq('active'),
            FilterExpression=Attr('rental_type').eq('subscription')  # Only subscription rentals
        )

        rentals = response.get('Items', [])
        invoices_created = 0

        print(f"Processing {len(rentals)} active subscription rentals for billing period {billing_period}")

        for rental in rentals:
            try:
                # Check if invoice already exists for this rental and billing period
                # (Idempotency check in case function is triggered multiple times)
                existing_invoice = invoices_table.query(
                    IndexName='rental-index',
                    KeyConditionExpression=Key('rental_id').eq(rental['rental_id']),
                    FilterExpression=Attr('billing_period').eq(billing_period)
                )

                if existing_invoice.get('Items'):
                    print(f"Invoice already exists for rental {rental['rental_id']} in period {billing_period}")
                    continue

                # Create invoice
                invoice_id = str(uuid.uuid4())

                invoice = {
                    'invoice_id': invoice_id,
                    'user_id': rental['user_id'],
                    'rental_id': rental['rental_id'],
                    'unit_id': rental['unit_id'],
                    'facility_id': rental['facility_id'],
                    'amount': rental['monthly_price'],
                    'status': 'pending',
                    'billing_period': billing_period,
                    'due_date': due_date,
                    'created_at': now.isoformat(),
                    'payment_attempts': 0
                }

                invoices_table.put_item(Item=invoice)
                invoices_created += 1

                print(f"Invoice created: {invoice_id} for rental {rental['rental_id']}")

            except Exception as rental_error:
                # Continue processing other rentals if one fails
                print(f"Error creating invoice for rental {rental.get('rental_id')}: {str(rental_error)}")
                continue

        message = f"Billing cycle completed. {invoices_created} invoices created for period {billing_period}."
        print(message)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": message,
                "invoices_created": invoices_created,
                "billing_period": billing_period
            })
        }

    except Exception as e:
        print(f"Error in recurring billing: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
