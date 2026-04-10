from django.contrib import admin

from .models import IntegrationJob


@admin.register(IntegrationJob)
class IntegrationJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "integration",
        "status",
        "scheduled_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("integration__user__username", "integration__external_id")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("integration", "message")
