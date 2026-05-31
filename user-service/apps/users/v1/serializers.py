from rest_framework import serializers

from apps.users.models import InterestMaster, UserMainDetails, UserPhoto, UserPreference


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


class InterestMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestMaster
        fields = ["id", "name", "emoji", "category"]


class SelectInterestsSerializer(serializers.Serializer):
    interest_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=5,
        error_messages={"min_length": "Select at least 5 interests."},
    )


class PreferenceSerializer(serializers.ModelSerializer):
    """Step 5 — user preferences."""

    class Meta:
        model = UserPreference
        fields = ["min_age", "max_age", "max_distance_km", "relationship_goal"]
        extra_kwargs = {
            "min_age": {"required": True},
            "max_age": {"required": True},
            "max_distance_km": {"required": True},
            "relationship_goal": {"required": True},
        }

    def validate(self, data):
        """Validate age range."""
        min_age = data.get("min_age")
        max_age = data.get("max_age")

        if min_age and max_age and min_age > max_age:
            raise serializers.ValidationError(
                {"min_age": "Minimum age cannot be greater than maximum age."}
            )

        if min_age and min_age < 18:
            raise serializers.ValidationError(
                {"min_age": "Minimum age must be at least 18."}
            )

        if max_age and max_age > 100:
            raise serializers.ValidationError(
                {"max_age": "Maximum age cannot exceed 100."}
            )

        return data
