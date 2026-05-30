import uuid
import bcrypt
from django.db import models


class UserMainDetails(models.Model):
    """
    Core user profile table. Stores identity and profile data.
    Authentication (password, tokens) lives in the accounts app.
    """

    class GenderChoices(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        UNDISCLOSED = 'U', 'Undisclosed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    gender = models.CharField(
        max_length=20,
        choices=GenderChoices.choices,
        default=GenderChoices.UNDISCLOSED,
    )

    # bcrypt hash — includes algorithm + salt + hash, no separate salt column needed
    password_hash = models.CharField(max_length=255)

    class Meta:
        db_table = 'user_main_details'
        verbose_name = 'User Main Details'
        verbose_name_plural = 'User Main Details'

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def set_password(self, raw_password: str) -> None:
        """Hash raw_password with bcrypt (cost factor 12) and store it."""
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), salt
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        """Return True if raw_password matches the stored bcrypt hash."""
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )
