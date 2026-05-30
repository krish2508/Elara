from rest_framework import serializers

from apps.users.models import UserMainDetails


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only public profile."""

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
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Writable fields the user can update on their own profile."""

    class Meta:
        model = UserMainDetails
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "birth_date",
            "biography",
            "gender",
        ]
