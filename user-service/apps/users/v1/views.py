from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.auth import authenticate
from .serializers import UpdateProfileSerializer, UserProfileSerializer


@api_view(["GET"])
@authenticate
def me(request: Request) -> Response:
    """
    GET /v1/users/me/
    Returns the authenticated user's profile.
    """
    return Response(
        UserProfileSerializer(request.user).data,
        status=status.HTTP_200_OK,
    )


@api_view(["PATCH"])
@authenticate
def update_me(request: Request) -> Response:
    """
    PATCH /v1/users/me/update/
    Update the authenticated user's profile fields.
    """
    serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    serializer.save()
    return Response(
        UserProfileSerializer(request.user).data,
        status=status.HTTP_200_OK,
    )
