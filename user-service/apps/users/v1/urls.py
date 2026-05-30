from django.urls import path
from . import views

urlpatterns = [
    path("me/", views.me, name="v1-users-me"),
    path("me/update/", views.update_me, name="v1-users-me-update"),
]
