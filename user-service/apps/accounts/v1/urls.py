from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="v1-auth-signup"),
    path("login/", views.login, name="v1-auth-login"),
    path("refresh/", views.refresh, name="v1-auth-refresh"),
    path("logout/", views.logout, name="v1-auth-logout"),
]
