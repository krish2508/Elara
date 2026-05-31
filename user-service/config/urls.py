from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "healthy", "service": "user-service"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("v1/auth/", include("apps.accounts.v1.urls")),
    path("v1/", include("apps.users.v1.urls")),
]
