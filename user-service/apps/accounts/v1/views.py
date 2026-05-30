from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import LoginSerializer, RefreshTokenSerializer, SignupSerializer
from .services import AuthService


def _get_client_meta(request: Request) -> tuple[str | None, str | None]:
    """Extract User-Agent and real IP (proxy-aware) from the request."""
    user_agent = request.META.get("HTTP_USER_AGENT")
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    return user_agent, ip_address


@api_view(["POST"])
def signup(request: Request) -> Response:
    """
    POST /v1/auth/signup/
    Body: { "email": "...", "password": "...", "name": "..." }
    """
    serializer = SignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    user_agent, ip_address = _get_client_meta(request)

    try:
        tokens = AuthService.signup(
            serializer.validated_data,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

    return Response(tokens, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login(request: Request) -> Response:
    """
    POST /v1/auth/login/
    Body: { "email": "...", "password": "..." }
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    user_agent, ip_address = _get_client_meta(request)

    try:
        tokens = AuthService.login(
            serializer.validated_data,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(tokens, status=status.HTTP_200_OK)


@api_view(["POST"])
def refresh(request: Request) -> Response:
    """
    POST /v1/auth/refresh/
    Body: { "refresh_token": "..." }
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        tokens = AuthService.refresh(serializer.validated_data["refresh_token"])
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(tokens, status=status.HTTP_200_OK)


@api_view(["POST"])
def logout(request: Request) -> Response:
    """
    POST /v1/auth/logout/
    Body: { "refresh_token": "..." }
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        AuthService.logout(serializer.validated_data["refresh_token"])
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
