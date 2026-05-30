import uuid
import bcrypt
from django.db import models


class OnboardingStep(models.IntegerChoices):
    """
    Numeric onboarding steps. Signup sets the user to step 0 (account created).
    Each subsequent screen increments the step until COMPLETED.

    0 — Account created (just signed up)
    1 — Basic profile  (name, gender, birth date)
    2 — Photos         (upload at least one photo)
    3 — Interests      (pick interest tags)
    4 — Preferences    (interested_in, distance, age range, etc.)
    5 — Completed      (onboarding done, enter the app)
    """
    ACCOUNT_CREATED       = 0, "Account Created"
    BASIC_PROFILE         = 1, "Basic Profile"
    PHOTOS                = 2, "Photos"
    INTERESTS             = 3, "Interests"
    PREFERENCES           = 4, "Preferences"
    COMPLETED             = 5, "Completed"


# Maps each step to the next one in the flow.
# Returns None when already at COMPLETED.
ONBOARDING_FLOW: dict[int, int | None] = {
    OnboardingStep.ACCOUNT_CREATED: OnboardingStep.BASIC_PROFILE,
    OnboardingStep.BASIC_PROFILE:   OnboardingStep.PHOTOS,
    OnboardingStep.PHOTOS:          OnboardingStep.INTERESTS,
    OnboardingStep.INTERESTS:       OnboardingStep.PREFERENCES,
    OnboardingStep.PREFERENCES:     OnboardingStep.COMPLETED,
    OnboardingStep.COMPLETED:       None,
}


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
        null=True,  # set during step 4 (Preferences)
    )

    onboarding_step = models.IntegerField(
        choices=OnboardingStep.choices,
        default=OnboardingStep.ACCOUNT_CREATED,
    )

    # bcrypt hash — includes algorithm + salt + hash, no separate salt column needed
    password_hash = models.CharField(max_length=255)

    class Meta:
        db_table = 'user_main_details'
        verbose_name = 'User Main Details'
        verbose_name_plural = 'User Main Details'

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

    def advance_onboarding(self) -> bool:
        """
        Move to the next onboarding step and save.
        Returns True if advanced, False if already completed.
        """
        next_step = ONBOARDING_FLOW.get(self.onboarding_step)
        if next_step is None:
            return False
        self.onboarding_step = next_step
        self.save(update_fields=["onboarding_step", "updated_at"])
        return True

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
