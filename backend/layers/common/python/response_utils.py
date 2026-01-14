"""
Standard response utilities for Lambda functions.
Provides consistent response formatting across all APIs.
"""

import json
from decimal import Decimal
from datetime import datetime, date


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)


def success_response(data: dict, status_code: int = 200) -> dict:
    """Generate a successful API response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(data, cls=DecimalEncoder)
    }


def error_response(error: str, message: str = None, status_code: int = 400) -> dict:
    """Generate an error API response."""
    body = {"error": error}
    if message:
        body["message"] = message

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def validation_error(message: str) -> dict:
    """Generate a 400 validation error response."""
    return error_response("Validation Error", message, 400)


def unauthorized_error(message: str = "Authentication required") -> dict:
    """Generate a 401 unauthorized error response."""
    return error_response("Unauthorized", message, 401)


def forbidden_error(message: str = "Access denied") -> dict:
    """Generate a 403 forbidden error response."""
    return error_response("Forbidden", message, 403)


def not_found_error(resource: str) -> dict:
    """Generate a 404 not found error response."""
    return error_response("Not Found", f"{resource} not found", 404)


def server_error(message: str = "Internal server error") -> dict:
    """Generate a 500 server error response."""
    return error_response("Internal Server Error", message, 500)
