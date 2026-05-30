from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.auth import authenticate
from apps.users.models import ONBOARDING_FLOW, OnboardingStep
from .serializers import CompleteProfileSerializer, UserProfileSerializer


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


@api_view(["POST"])
@authenticate
def complete_profile(request: Request) -> Response:
    """
    POST /v1/users/profile/

    Onboarding step 1 — submit basic profile info.
    Accepts: first_name, last_name, birth_date, gender, interested_in.
    Advances onboarding_step from 0 (ACCOUNT_CREATED) → 1 (BASIC_PROFILE).
    """
    user = request.user

    if user.onboarding_step != OnboardingStep.ACCOUNT_CREATED:
        return Response(
            {
                "detail": "Profile already completed.",
                "current_onboarding_step": user.onboarding_step,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CompleteProfileSerializer(user, data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Save profile fields and advance to step 1
    user = serializer.save(
        onboarding_step=ONBOARDING_FLOW[OnboardingStep.ACCOUNT_CREATED]
    )

    return Response(
        UserProfileSerializer(user).data,
        status=status.HTTP_200_OK,
    )
