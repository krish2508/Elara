"""
Authentication decorator for DRF function-based views.

Usage
-----
    from apps.core.auth import authenticate

    @api_view(["GET"])
    @authenticate
    def my_view(request):
        user = request.user   # UserMainDetails instance, always set here
        ...

Token must be passed as a custom header:
    access-token: <token>
"""

from functools import wraps

import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from apps.users.models import UserMainDetails


def _extract_token(request) -> str | None:
    """
    Pull the raw JWT string from the 'access-token' header.
    Django converts headers to META keys as:
      HTTP_<HEADER_NAME_UPPERCASED_WITH_UNDERSCORES>
    So 'access-token' → 'HTTP_ACCESS_TOKEN'
    """
    return request.META.get("HTTP_ACCESS_TOKEN", "").strip() or None


def authenticate(view_func):
    """
    Decorator that verifies the access token and injects the authenticated
    user into request.user before calling the view.

    Returns 401 immediately if the token is missing, invalid, or expired.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = _extract_token(request)

        if not token:
            return Response(
                {"detail": "Authentication token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"detail": "Access token has expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError:
            return Response(
                {"detail": "Invalid access token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if payload.get("type") != "access":
            return Response(
                {"detail": "Invalid token type."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = UserMainDetails.objects.get(id=payload["sub"], is_active=True)
        except UserMainDetails.DoesNotExist:
            return Response(
                {"detail": "User not found or account deactivated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Attach user to request so the view can access it via request.user
        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapper
