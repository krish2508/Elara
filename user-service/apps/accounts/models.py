import uuid
from django.db import models


class RefreshToken(models.Model):
    """
    Persisted refresh tokens — one row per active session.
    Supports rotation (old token invalidated on use) and revocation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "users.UserMainDetails",
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    # JTI (JWT ID) — lets us look up / revoke without storing the full token string
    jti = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    # Optional device metadata for security dashboards
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'refresh_tokens'
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'

    def __str__(self):
        return f"RefreshToken(user={self.user.email}, jti={self.jti[:8]}…)"
