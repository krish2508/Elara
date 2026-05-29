import uuid
from django.db import models

class UserMainDetails(models.Model):
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
    gender = models.CharField(
        max_length=20,
        choices=GenderChoices.choices,
        default=GenderChoices.UNDISCLOSED
    )

    class Meta:
        db_table = 'user_main_details'
        verbose_name = 'User Main Details'
        verbose_name_plural = 'User Main Details'

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"

