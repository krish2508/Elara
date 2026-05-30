import uuid
import bcrypt
from django.db import models


class OnboardingStep(models.IntegerChoices):
    ACCOUNT_CREATED = 0, "Account Created"
    BASIC_PROFILE   = 1, "Basic Profile"
    PHOTOS          = 2, "Photos"
    INTERESTS       = 3, "Interests"
    PREFERENCES     = 4, "Preferences"
    COMPLETED       = 5, "Completed"


ONBOARDING_FLOW: dict[int, int | None] = {
    OnboardingStep.ACCOUNT_CREATED: OnboardingStep.BASIC_PROFILE,
    OnboardingStep.BASIC_PROFILE:   OnboardingStep.PHOTOS,
    OnboardingStep.PHOTOS:          OnboardingStep.INTERESTS,
    OnboardingStep.INTERESTS:       OnboardingStep.PREFERENCES,
    OnboardingStep.PREFERENCES:     OnboardingStep.COMPLETED,
    OnboardingStep.COMPLETED:       None,
}


class UserMainDetails(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        UNDISCLOSED = 'U', 'Undisclosed'

    class InterestedInChoices(models.TextChoices):
        MALE   = 'M', 'Male'
        FEMALE = 'F', 'Female'
        BOTH   = 'B', 'Both'

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
        max_length=1,
        choices=GenderChoices.choices,
        default=GenderChoices.UNDISCLOSED,
    )
    interested_in = models.CharField(
        max_length=1,
        choices=InterestedInChoices.choices,
        blank=True,
        null=True,
    )
    onboarding_step = models.IntegerField(
        choices=OnboardingStep.choices,
        default=OnboardingStep.ACCOUNT_CREATED,
    )
    password_hash = models.CharField(max_length=255)

    class Meta:
        db_table = 'user_main_details'
        verbose_name = 'User Main Details'
        verbose_name_plural = 'User Main Details'

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def set_password(self, raw_password: str) -> None:
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), salt
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )


class UserPhoto(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
        UserMainDetails,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image_url   = models.URLField()
    order_index = models.PositiveSmallIntegerField()
    is_primary  = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_photos'
        ordering = ["order_index"]
        verbose_name = 'User Photo'
        verbose_name_plural = 'User Photos'

    def __str__(self):
        return f"Photo({self.user.email}, order={self.order_index})"
