from django.contrib.auth.models import AbstractUser
from django.db import models

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

    def __str__(self):
        return self.username
