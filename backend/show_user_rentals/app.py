import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')
facilities_table = dynamodb.Table('Facilities')

def lambda_handler(event, context):
    try:
        # Get user_id from query parameters
        user_id = event['queryStringParameters']['user_id']

        # Query Rentals table for this user
        response = rentals_table.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )

        rentals = response.get('Items', [])

        # Enrich rentals with unit and facility details
        enriched_rentals = []
        for rental in rentals:
            unit_id = rental.get('unit_id')
            facility_id = rental.get('facility_id')

            # Get unit details
            if unit_id:
                unit_response = units_table.get_item(Key={'unit_id': unit_id})
                rental['unit_details'] = unit_response.get('Item', {})

            # Get facility details
            if facility_id:
                facility_response = facilities_table.get_item(Key={'facility_id': facility_id})
                rental['facility_details'] = facility_response.get('Item', {})

            enriched_rentals.append(rental)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "rentals": enriched_rentals,
                "count": len(enriched_rentals)
            })
        }

    except KeyError:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Missing user_id parameter"
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
                "error": "Failed to retrieve user rentals",
                "message": str(e)
            })
        }
