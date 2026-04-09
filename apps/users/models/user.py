from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.core.constants import ChatMode


class User(AbstractUser):
    chat_mode = models.CharField(
        max_length=20,
        choices=ChatMode.choices,
        null=True,
        blank=True,
    )
    opted_in_at = models.DateTimeField(null=True, blank=True)
    opted_out_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_opted_in(self):
        return self.opted_in_at is not None and self.opted_out_at is None

    def activate(self, mode: str) -> None:
        self.chat_mode = mode
        self.opted_in_at = timezone.now()
        self.opted_out_at = None
        self.save(
            update_fields=["chat_mode", "opted_in_at", "opted_out_at", "updated_at"]
        )

    def deactivate(self) -> None:
        self.opted_out_at = timezone.now()
        self.save(update_fields=["opted_out_at", "updated_at"])

    def switch_mode(self, mode: str) -> str:
        """Switch chat mode, returning the previous mode."""
        old_mode = self.chat_mode
        self.chat_mode = mode
        self.save(update_fields=["chat_mode", "updated_at"])
        return old_mode

    def __str__(self):
        return self.username
