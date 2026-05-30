from rest_framework import serializers

from apps.users.models import UserMainDetails


class CompleteProfileSerializer(serializers.ModelSerializer):
    """
    Step 1 of onboarding — collect basic profile info.
    All fields required at this step.
    """

    class Meta:
        model = UserMainDetails
        fields = [
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "interested_in",
        ]
        extra_kwargs = {
            "first_name":   {"required": True},
            "last_name":    {"required": True},
            "birth_date":   {"required": True},
            "gender":       {"required": True},
            "interested_in": {"required": True},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile — returned after any profile read or update."""

    class Meta:
        model = UserMainDetails
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "birth_date",
            "biography",
            "gender",
            "interested_in",
            "onboarding_step",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
