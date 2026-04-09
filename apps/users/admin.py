from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserIntegration


class UserIntegrationInline(admin.TabularInline):
    model = UserIntegration
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "first_name", "last_name", "email", "chat_mode", "is_opted_in", "created_at")
    list_filter = ("chat_mode", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [UserIntegrationInline]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Daily Notetaker", {"fields": ("chat_mode", "opted_in_at", "opted_out_at", "metadata", "created_at", "updated_at")}),
    )


@admin.register(UserIntegration)
class UserIntegrationAdmin(admin.ModelAdmin):
    list_display = ("user", "vendor", "external_id", "created_at")
    list_filter = ("vendor",)
    search_fields = ("user__username", "external_id")
    readonly_fields = ("created_at", "updated_at")
