from django.contrib import admin

from .models import Message, Session


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "template_key", "created_at")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "chat_mode", "status", "created_at")
    list_filter = ("chat_mode", "status")
    search_fields = ("user__username",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "template_key", "created_at")
    list_filter = ("role",)
    search_fields = ("content", "session__user__username")
    readonly_fields = ("created_at", "updated_at")
