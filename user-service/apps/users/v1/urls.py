from django.urls import path
from . import views

urlpatterns = [
    # Profile
    path("users/me/", views.me, name="v1-users-me"),
    path("users/profile/", views.complete_profile, name="v1-users-complete-profile"),
    # Biography
    path("users/profile/biography/", views.save_biography, name="v1-users-biography"),
    path(
        "users/profile/biography/generate/",
        views.generate_biography,
        name="v1-users-biography-generate",
    ),
    # Photos
    path("photos/", views.photos, name="v1-photos"),
    path("photos/<uuid:photo_id>/", views.delete_photo_view, name="v1-photos-delete"),
    # Onboarding
    path(
        "onboarding/photos/complete/",
        views.photos_complete,
        name="v1-onboarding-photos-complete",
    ),
]
