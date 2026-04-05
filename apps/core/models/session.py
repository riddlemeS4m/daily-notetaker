from django.db import models

from apps.core.constants import ChatMode
from apps.users.models import User


class Session(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        AWAITING_RESPONSE = "awaiting_response", "Awaiting Response"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    chat_mode = models.CharField(max_length=20, choices=ChatMode.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def close_all_open(cls, user, chat_mode=None):
        qs = cls.objects.filter(
            user=user,
            status__in=[cls.Status.ACTIVE, cls.Status.AWAITING_RESPONSE],
        )
        if chat_mode:
            qs = qs.filter(chat_mode=chat_mode)
        return qs.update(status=cls.Status.CLOSED)

    def __str__(self):
        return f"Session({self.user}, {self.chat_mode}, {self.status})"
