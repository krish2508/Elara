"""
AuthService — signup, login, token refresh, and logout.

Token strategy
--------------
- Access token  : short-lived JWT (15 min), signed with HS256.
- Refresh token : long-lived JWT (7 days), signed with HS256.
                  The JTI (JWT ID) is persisted in the DB so tokens can be
                  rotated and revoked server-side.

Password hashing
----------------
bcrypt with cost factor 12.  The full "$2b$12$…" string (algorithm + salt +
hash) is stored in UserMainDetails.password_hash — no separate salt column
needed because bcrypt embeds the salt in the hash string.
"""

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from django.conf import settings
from django.db import transaction

from apps.accounts.models import RefreshToken
from apps.users.models import UserMainDetails

# ---------------------------------------------------------------------------
# Constants (override via settings if needed)
# ---------------------------------------------------------------------------

ACCESS_TOKEN_TTL: int = getattr(settings, "ACCESS_TOKEN_TTL_SECONDS", 15 * 60)
REFRESH_TOKEN_TTL: int = getattr(settings, "REFRESH_TOKEN_TTL_SECONDS", 7 * 24 * 3600)
JWT_ALGORITHM = "HS256"

# Dummy hash used for constant-time response on unknown emails
_DUMMY_HASH = b"$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_secret() -> str:
    secret = settings.SECRET_KEY
    if not secret:
        raise RuntimeError("SECRET_KEY is not configured.")
    return secret


def _issue_access_token(user: UserMainDetails) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(seconds=ACCESS_TOKEN_TTL),
        "type": "access",
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def _issue_refresh_token(
    user: UserMainDetails,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, RefreshToken]:
    """
    Create a signed refresh JWT and persist its JTI in the DB.
    Returns (token_string, RefreshToken_instance).
    """
    now = datetime.now(tz=timezone.utc)
    jti = secrets.token_hex(32)  # 64-char hex, cryptographically random
    expires_at = now + timedelta(seconds=REFRESH_TOKEN_TTL)

    payload = {
        "sub": str(user.id),
        "jti": jti,
        "iat": now,
        "exp": expires_at,
        "type": "refresh",
    }
    token_str = jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)

    db_token = RefreshToken.objects.create(
        user=user,
        jti=jti,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    return token_str, db_token


def _build_token_response(access: str, refresh: str) -> dict:
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL,
    }


# ---------------------------------------------------------------------------
# Public service
# ---------------------------------------------------------------------------


class AuthService:

    # ------------------------------------------------------------------
    # Signup
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def signup(
        data: dict,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        """
        Create a new user and return a token pair.

        Raises
        ------
        ValueError  — if the email is already registered.
        """
        email = data["email"].lower().strip()

        if UserMainDetails.objects.filter(email=email).exists():
            raise ValueError("An account with this email already exists.")

        user = UserMainDetails(email=email)
        user.set_password(data["password"])  # bcrypt hash stored here
        user.save()

        access = _issue_access_token(user)
        refresh, _ = _issue_refresh_token(user, user_agent, ip_address)

        return _build_token_response(access, refresh)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    @staticmethod
    def login(
        data: dict,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        """
        Authenticate a user and return a token pair.

        Raises
        ------
        ValueError  — on invalid credentials or inactive account.
        """
        email = data["email"].lower().strip()

        try:
            user = UserMainDetails.objects.get(email=email)
        except UserMainDetails.DoesNotExist:
            # Constant-time response — prevent user enumeration via timing
            bcrypt.checkpw(b"dummy", _DUMMY_HASH)
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise ValueError("This account has been deactivated.")

        if not user.check_password(data["password"]):
            raise ValueError("Invalid email or password.")

        access = _issue_access_token(user)
        refresh, _ = _issue_refresh_token(user, user_agent, ip_address)

        return _build_token_response(access, refresh)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def refresh(refresh_token_str: str) -> dict:
        """
        Validate a refresh token, rotate it (revoke old, issue new), and
        return a new token pair.

        Raises
        ------
        ValueError  — if the token is invalid, expired, or already revoked.
        """
        try:
            payload = jwt.decode(
                refresh_token_str,
                _get_secret(),
                algorithms=[JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token.")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type.")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        try:
            db_token = RefreshToken.objects.select_for_update().get(jti=jti)
        except RefreshToken.DoesNotExist:
            raise ValueError("Refresh token not found.")

        if db_token.revoked:
            # Token reuse detected — revoke ALL sessions for this user
            RefreshToken.objects.filter(user_id=user_id).update(revoked=True)
            raise ValueError(
                "Refresh token already used. All sessions have been invalidated."
            )

        # Rotate: revoke the old token
        db_token.revoked = True
        db_token.save(update_fields=["revoked"])

        user = db_token.user
        if not user.is_active:
            raise ValueError("This account has been deactivated.")

        access = _issue_access_token(user)
        refresh, _ = _issue_refresh_token(
            user,
            user_agent=db_token.user_agent,
            ip_address=db_token.ip_address,
        )

        return _build_token_response(access, refresh)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    @staticmethod
    def logout(refresh_token_str: str) -> None:
        """
        Revoke a specific refresh token (single-device logout).

        Raises
        ------
        ValueError  — if the token is invalid or not found.
        """
        try:
            payload = jwt.decode(
                refresh_token_str,
                _get_secret(),
                algorithms=[JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token.")

        jti = payload.get("jti")
        updated = RefreshToken.objects.filter(jti=jti, revoked=False).update(
            revoked=True
        )
        if not updated:
            raise ValueError("Token not found or already revoked.")

    # ------------------------------------------------------------------
    # Logout all devices
    # ------------------------------------------------------------------

    @staticmethod
    def logout_all(user_id: str) -> None:
        """Revoke every active refresh token for a user (all-device logout)."""
        RefreshToken.objects.filter(user_id=user_id, revoked=False).update(revoked=True)
