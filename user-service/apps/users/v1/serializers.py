from rest_framework import serializers

from apps.users.models import UserMainDetails, UserPhoto


class CompleteProfileSerializer(serializers.ModelSerializer):
    """Step 1 — basic profile info."""

    class Meta:
        model = UserMainDetails
        fields = ["first_name", "last_name", "birth_date", "gender", "interested_in"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
            "birth_date": {"required": True},
            "gender": {"required": True},
            "interested_in": {"required": True},
        }


class BiographySerializer(serializers.ModelSerializer):
    """Step 3 — biography."""

    class Meta:
        model = UserMainDetails
        fields = ["biography"]
        extra_kwargs = {"biography": {"required": True}}


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile read."""

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


class UserPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoto
        fields = ["id", "image_url", "order_index", "is_primary", "created_at"]
        read_only_fields = fields
