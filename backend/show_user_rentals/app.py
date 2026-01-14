"""
Show User Rentals - Retrieve all rentals for authenticated user with enriched details.
Admins can query any user's rentals by providing user_id query parameter.
"""

import boto3
from boto3.dynamodb.conditions import Key

from auth_utils import require_auth
from response_utils import success_response, forbidden_error, server_error

dynamodb = boto3.resource('dynamodb')
rentals_table = dynamodb.Table('Rentals')
units_table = dynamodb.Table('Units')
facilities_table = dynamodb.Table('Facilities')


@require_auth
def lambda_handler(event, context):
    """
    Retrieve rentals for authenticated user or specified user (admin only).

    Query params:
        - user_id (optional): User ID to query (admin only)

    Returns:
        API response with list of rentals
    """
    try:
        authenticated_user_id = event['user_context']['user_id']
        user_type = event['user_context']['user_type']

        # Admins can query any user's rentals, clients only their own
        query_params = event.get('queryStringParameters') or {}
        query_user_id = query_params.get('user_id')

        if query_user_id and query_user_id != authenticated_user_id:
            # Another user's data requested - check admin permission
            if user_type != 'admin':
                return forbidden_error("Cannot view other users' rentals")
            user_id = query_user_id
        else:
            user_id = authenticated_user_id

        # Query rentals using GSI (efficient)
        response = rentals_table.query(
            IndexName='user-index',
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        rentals = response.get('Items', [])

        # Enrich rentals with unit and facility details
        enriched_rentals = []
        for rental in rentals:
            # Get unit details
            unit_response = units_table.get_item(Key={'unit_id': rental['unit_id']})
            rental['unit_details'] = unit_response.get('Item', {})

            # Get facility details
            facility_response = facilities_table.get_item(Key={'facility_id': rental['facility_id']})
            rental['facility_details'] = facility_response.get('Item', {})

            enriched_rentals.append(rental)

        print(f"Retrieved {len(enriched_rentals)} rentals for user {user_id}")

        return success_response({
            "rentals": enriched_rentals,
            "count": len(enriched_rentals)
        })

    except Exception as e:
        print(f"Error retrieving rentals: {str(e)}")
        return server_error()
