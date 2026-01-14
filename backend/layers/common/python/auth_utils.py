"""
Authentication and authorization utilities for Lambda functions.
Provides user context extraction from Cognito claims.
"""

import json
import os
from typing import Dict, Tuple
from functools import wraps


def extract_user_from_event(event: Dict) -> Tuple[str, str, str, str]:
    """
    Extract authenticated user information from API Gateway event with Cognito authorizer.

    Args:
        event: API Gateway event with Cognito authorizer context

    Returns:
        Tuple of (user_id, email, user_type, full_name)

    Raises:
        ValueError: If user context is missing or invalid
    """
    try:
        # Cognito authorizer adds claims to requestContext
        claims = event['requestContext']['authorizer']['claims']

        user_id = claims['sub']  # Cognito user ID (UUID)
        email = claims['email']
        user_type = claims.get('custom:user_type', 'client')  # Default to 'client'
        full_name = claims.get('custom:full_name', '')

        return user_id, email, user_type, full_name
    except (KeyError, TypeError) as e:
        raise ValueError(f"Missing or invalid Cognito claims in request context: {str(e)}")


def require_auth(handler):
    """
    Decorator to enforce authentication on Lambda handlers.
    Extracts user context and adds it to the event.

    Usage:
        @require_auth
        def lambda_handler(event, context):
            user_id = event['user_context']['user_id']
            user_type = event['user_context']['user_type']
            ...
    """
    @wraps(handler)
    def wrapper(event, context):
        try:
            user_id, email, user_type, full_name = extract_user_from_event(event)

            # Add user context to event for easy access
            event['user_context'] = {
                'user_id': user_id,
                'email': email,
                'user_type': user_type,
                'full_name': full_name
            }

            return handler(event, context)

        except ValueError as e:
            return {
                "statusCode": 401,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Unauthorized",
                    "message": str(e)
                })
            }

    return wrapper


def require_role(*allowed_roles):
    """
    Decorator to enforce role-based access control.

    Usage:
        @require_role('admin')
        def lambda_handler(event, context):
            # Only admin users can access this
            ...
    """
    def decorator(handler):
        @wraps(handler)
        def wrapper(event, context):
            try:
                user_id, email, user_type, full_name = extract_user_from_event(event)

                if user_type not in allowed_roles:
                    return {
                        "statusCode": 403,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                        },
                        "body": json.dumps({
                            "error": "Forbidden",
                            "message": f"Access denied. Required roles: {', '.join(allowed_roles)}"
                        })
                    }

                # Add user context to event
                event['user_context'] = {
                    'user_id': user_id,
                    'email': email,
                    'user_type': user_type,
                    'full_name': full_name
                }

                return handler(event, context)

            except ValueError as e:
                return {
                    "statusCode": 401,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({
                        "error": "Unauthorized",
                        "message": str(e)
                    })
                }

        return wrapper
    return decorator


def is_admin(event: Dict) -> bool:
    """Check if the authenticated user is an admin."""
    try:
        return event.get('user_context', {}).get('user_type') == 'admin'
    except Exception:
        return False


def owns_resource(event: Dict, resource_user_id: str) -> bool:
    """
    Check if the authenticated user owns a resource.
    Admins can access all resources.
    """
    try:
        user_id = event['user_context']['user_id']
        user_type = event['user_context']['user_type']

        return user_id == resource_user_id or user_type == 'admin'
    except Exception:
        return False
