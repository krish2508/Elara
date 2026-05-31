from django.contrib import admin

from .models import InterestMaster


@admin.register(InterestMaster)
class InterestMasterAdmin(admin.ModelAdmin):
    list_display  = ["name", "emoji", "category", "is_active", "created_at"]
    list_filter   = ["category", "is_active"]
    search_fields = ["name", "category"]
    ordering      = ["category", "name"]
