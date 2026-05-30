from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.auth import authenticate
from apps.users.v1.utils import get_photo_url, remove_photo, upload_photo
from apps.users.models import ONBOARDING_FLOW, OnboardingStep, UserPhoto
from .serializers import CompleteProfileSerializer, UserPhotoSerializer, UserProfileSerializer


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
    Onboarding step 1 — submit basic profile info.
    Advances onboarding_step: 0 → 1
    """
    user = request.user

    if user.onboarding_step != OnboardingStep.ACCOUNT_CREATED:
        return Response(
            {
                "detail": "Profile already completed.",
                "onboarding_step": user.onboarding_step,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CompleteProfileSerializer(user, data=request.data)
    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    user = serializer.save(onboarding_step=ONBOARDING_FLOW[OnboardingStep.ACCOUNT_CREATED])
    return Response(UserProfileSerializer(user).data)


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------

@api_view(["POST", "GET"])
@authenticate
@parser_classes([MultiPartParser])
def photos(request: Request) -> Response:
    """
    POST /v1/photos/  — upload a photo to GCP
    GET  /v1/photos/  — list all photos
    """
    if request.method == "GET":
        all_photos = request.user.photos.all()
        data = UserPhotoSerializer(all_photos, many=True).data
        # Attach a fresh signed URL to each photo
        for item, photo in zip(data, all_photos):
            item["signed_url"] = get_photo_url(photo.image_url)
        return Response(data)

    # POST — upload
    user = request.user
    file = request.FILES.get("photo")

    if not file:
        return Response({"detail": "No photo file provided."}, status=status.HTTP_400_BAD_REQUEST)

    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        return Response({"detail": "File must be an image."}, status=status.HTTP_400_BAD_REQUEST)

    last = user.photos.order_by("-order_index").first()
    order_index = (last.order_index + 1) if last else 0
    is_primary = order_index == 0

    image_url = upload_photo(file, str(user.id), content_type)

    photo = UserPhoto.objects.create(
        user=user,
        image_url=image_url,
        order_index=order_index,
        is_primary=is_primary,
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
        return Response({"detail": "Photo not found."}, status=status.HTTP_404_NOT_FOUND)

    # Delete from GCS then from DB
    remove_photo(photo.image_url)
    photo.delete()

    # If the deleted photo was primary, promote the next one
    remaining = request.user.photos.order_by("order_index").first()
    if remaining and not remaining.is_primary:
        remaining.is_primary = True
        remaining.save(update_fields=["is_primary"])
    data={"details":"photo deleteed successfully}"}
    return Response(data,status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Onboarding — photos complete
# ---------------------------------------------------------------------------

@api_view(["POST"])
@authenticate
def photos_complete(request: Request) -> Response:
    """
    POST /v1/onboarding/photos/complete/
    Continue button after photo upload step.
    Requires at least 2 photos. Advances onboarding_step: 2 → 3
    """
    user = request.user
    photo_count = user.photos.count()

    if photo_count < 2:
        return Response(
            {"error": "At least 2 photos required", "photo_count": photo_count},
            status=status.HTTP_400_BAD_REQUEST,
        )
    current_onboarding_step=user.onboarding_step
    if ONBOARDING_FLOW.get(current_onboarding_step) != OnboardingStep.PHOTOS:
        return Response(
            {
                "detail": "Not at the photos onboarding step.",
                "onboarding_step": user.onboarding_step,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.onboarding_step = OnboardingStep.PHOTOS
    user.save(update_fields=["onboarding_step", "updated_at"])

    return Response(
        {"onboarding_step": user.onboarding_step},
        status=status.HTTP_200_OK,
    )
