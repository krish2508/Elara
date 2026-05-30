from django.urls import path
from . import views

urlpatterns = [
    path("me/", views.me, name="v1-users-me"),
    path("profile/", views.complete_profile, name="v1-users-complete-profile"),
]
