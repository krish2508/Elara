from datetime import date

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.auth import authenticate
from apps.core.llm import call_llm
from apps.users.v1.utils import get_photo_url, remove_photo, upload_photo
from apps.users.models import (
    ONBOARDING_FLOW,
    InterestMaster,
    OnboardingStep,
    UserInterest,
    UserPhoto,
)
from .serializers import (
    BiographySerializer,
    CompleteProfileSerializer,
    InterestMasterSerializer,
    SelectInterestsSerializer,
    UserPhotoSerializer,
    UserProfileSerializer,
)


def _check_onboarding_step(user, expected_step: int):
    """
    Verify the user is at the correct onboarding step.

    Strategy:
      1. Get the user's current step.
      2. Look up what the NEXT step should be via ONBOARDING_FLOW.
      3. Compare that next step against expected_step.

    Returns an error Response if the check fails, otherwise None.
    """
    current = user.onboarding_step
    next_step = ONBOARDING_FLOW.get(current)

    if next_step != expected_step:
        return Response(
            {
                "detail": f"Expected to be at step {expected_step}, "
                f"but current step is {current}.",
                "onboarding_step": current,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    return None


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


@api_view(["GET"])
@authenticate
def me(request: Request) -> Response:
    """GET /v1/users/me/"""
    return Response(UserProfileSerializer(request.user).data)


@api_view(["POST"])
@authenticate
def complete_profile(request: Request) -> Response:
    """
    POST /v1/users/profile/
    Onboarding step 0 → 1 (ACCOUNT_CREATED → BASIC_PROFILE)
    """
    error = _check_onboarding_step(request.user, OnboardingStep.BASIC_PROFILE)
    if error:
        return error

    serializer = CompleteProfileSerializer(request.user, data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    user = serializer.save(
        onboarding_step=ONBOARDING_FLOW[OnboardingStep.ACCOUNT_CREATED]
    )
    return Response(UserProfileSerializer(user).data)


# ---------------------------------------------------------------------------
# Biography
# ---------------------------------------------------------------------------


@api_view(["POST"])
@authenticate
def save_biography(request: Request) -> Response:
    """
    POST /v1/users/profile/biography/
    Onboarding step 2 → 3 (PHOTOS → BIOGRAPHY)
    """
    error = _check_onboarding_step(request.user, OnboardingStep.BIOGRAPHY)
    if error:
        return error

    serializer = BiographySerializer(request.user, data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    user = serializer.save(onboarding_step=OnboardingStep.BIOGRAPHY)
    return Response(UserProfileSerializer(user).data)


@api_view(["POST"])
@authenticate
def generate_biography(request: Request) -> Response:
    """
    POST /v1/users/profile/biography/generate/
    Generate a biography suggestion via Gemini. Does NOT save.
    Optional body: { "hints": "loves hiking, software engineer" }
    """
    user = request.user
    hints = request.data.get("hints", "").strip()

    age = ""
    if user.birth_date:
        age_years = (date.today() - user.birth_date).days // 365
        age = f"{age_years}-year-old"

    gender_label = user.get_gender_display() if user.gender else ""
    name = user.first_name or "this person"

    prompt_parts = [
        f"Write a short, warm, and authentic dating app biography for {name}.",
        f"They are a {age} {gender_label}." if age or gender_label else "",
        f"Additional details: {hints}" if hints else "",
        "Keep it under 50 words. First person. No hashtags. Sound natural and genuine.",
    ]
    prompt = " ".join(p for p in prompt_parts if p)

    try:
        suggestion = call_llm(prompt)
    except Exception as exc:
        return Response(
            {"detail": f"AI generation failed: {str(exc)}"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response({"biography": suggestion}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------


@api_view(["POST", "GET"])
@authenticate
@parser_classes([MultiPartParser])
def photos(request: Request) -> Response:
    """
    GET  /v1/photos/ — list all photos with signed URLs
    POST /v1/photos/ — upload a photo to GCS
    """
    if request.method == "GET":
        all_photos = request.user.photos.all()
        data = UserPhotoSerializer(all_photos, many=True).data
        for item, photo in zip(data, all_photos):
            item["signed_url"] = get_photo_url(photo.image_url)
        return Response(data)

    # POST — upload
    user = request.user
    file = request.FILES.get("photo")

    if not file:
        return Response(
            {"detail": "No photo file provided."}, status=status.HTTP_400_BAD_REQUEST
        )

    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        return Response(
            {"detail": "File must be an image."}, status=status.HTTP_400_BAD_REQUEST
        )

    last = user.photos.order_by("-order_index").first()
    order_index = (last.order_index + 1) if last else 0

    image_url = upload_photo(file, str(user.id), content_type)
    photo = UserPhoto.objects.create(
        user=user,
        image_url=image_url,
        order_index=order_index,
        is_primary=(order_index == 0),
    )

    data = UserPhotoSerializer(photo).data
    data["signed_url"] = get_photo_url(photo.image_url)
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@authenticate
def delete_photo_view(request: Request, photo_id: str) -> Response:
    """DELETE /v1/photos/<photo_id>/"""
    try:
        photo = UserPhoto.objects.get(id=photo_id, user=request.user)
    except UserPhoto.DoesNotExist:
        return Response(
            {"detail": "Photo not found."}, status=status.HTTP_404_NOT_FOUND
        )

    remove_photo(photo.image_url)
    photo.delete()

    remaining = request.user.photos.order_by("order_index").first()
    if remaining and not remaining.is_primary:
        remaining.is_primary = True
        remaining.save(update_fields=["is_primary"])

    return Response(
        {"details": "photo deleteed successfully}"}, status=status.HTTP_204_NO_CONTENT
    )


@api_view(["POST"])
@authenticate
def photos_complete(request: Request) -> Response:
    """
    POST /v1/onboarding/photos/complete/
    Onboarding step 2 → 3 (PHOTOS → BIOGRAPHY). Requires ≥ 2 photos.
    """
    user = request.user

    error = _check_onboarding_step(user, OnboardingStep.BIOGRAPHY)
    if error:
        return error

    photo_count = user.photos.count()
    if photo_count < 2:
        return Response(
            {"error": "At least 2 photos required.", "photo_count": photo_count},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.onboarding_step = ONBOARDING_FLOW[OnboardingStep.PHOTOS]
    user.save(update_fields=["onboarding_step", "updated_at"])

    return Response({"onboarding_step": user.onboarding_step})


# ---------------------------------------------------------------------------
# Interests
# ---------------------------------------------------------------------------


@api_view(["GET", "POST"])
@authenticate
def interests(request: Request) -> Response:
    """
    GET  /v1/interests/ — list all active interests from master table
    POST /v1/interests/ — select interests (onboarding step 4 → 5)
    """
    if request.method == "GET":
        all_interests = InterestMaster.objects.filter(is_active=True)
        return Response(InterestMasterSerializer(all_interests, many=True).data)

    return select_interests(request)


@transaction.atomic
def select_interests(request: Request) -> Response:
    """
    POST /v1/interests/
    Onboarding step 4 → 5 (INTERESTS → PREFERENCES).

    Body: { "interest_ids": ["uuid1", "uuid2", ...] }  — minimum 5

    Steps:
      1. Check user is at the INTERESTS onboarding step.
      2. Validate all provided IDs exist in InterestMaster.
      3. Delete existing UserInterest rows for this user.
      4. Bulk-insert the new selections.
      5. Advance onboarding step.
    """
    user = request.user

    error = _check_onboarding_step(user, OnboardingStep.INTERESTS)
    if error:
        return error

    serializer = SelectInterestsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    interest_ids = serializer.validated_data["interest_ids"]

    # Validate all IDs exist and are active
    valid_interests = InterestMaster.objects.filter(id__in=interest_ids, is_active=True)
    if valid_interests.count() != len(interest_ids):
        found_ids = set(str(i.id) for i in valid_interests)
        invalid = [str(i) for i in interest_ids if str(i) not in found_ids]
        return Response(
            {"detail": "Some interest IDs are invalid.", "invalid_ids": invalid},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Replace existing selections atomically
    UserInterest.objects.filter(user=user).delete()
    UserInterest.objects.bulk_create(
        [UserInterest(user=user, interest=interest) for interest in valid_interests]
    )

    # Advance onboarding
    user.onboarding_step = ONBOARDING_FLOW[OnboardingStep.INTERESTS]
    user.save(update_fields=["onboarding_step", "updated_at"])

    return Response(
        {
            "onboarding_step": user.onboarding_step,
            "interests": InterestMasterSerializer(valid_interests, many=True).data,
        },
        status=status.HTTP_200_OK,
    )
