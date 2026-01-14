"""
Show Facility Availability - Public endpoint to view available units in a facility.
No authentication required.
"""

import json
import boto3
from boto3.dynamodb.conditions import Key

from response_utils import success_response, not_found_error, server_error

dynamodb = boto3.resource('dynamodb')
units_table = dynamodb.Table('Units')


def lambda_handler(event, context):
    """
    Retrieve available units for a facility.

    Path params:
        - facility_id: ID of the facility

    Returns:
        List of available units in the facility
    """
    try:
        facility_id = event['pathParameters']['facility_id']

        # Query units by facility with status filter using GSI (efficient)
        response = units_table.query(
            IndexName='facility-status-index',
            KeyConditionExpression=Key('facility_id').eq(facility_id) & Key('status').eq('available')
        )

        units = response.get('Items', [])

        print(f"Found {len(units)} available units in facility {facility_id}")

        return success_response({
            "facility_id": facility_id,
            "available_units": units,
            "count": len(units)
        })

    except KeyError:
        return not_found_error("Facility")
    except Exception as e:
        print(f"Error retrieving facility availability: {str(e)}")
        return server_error()
