from django.db import models

from .session import Session


class Message(models.Model):
    class Role(models.TextChoices):
        BOT = "bot", "Bot"
        USER = "user", "User"

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    template_key = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def _validate_role(cls, role: str) -> None:
        if role not in cls.Role.values:
            raise ValueError(
                f"Role must be one of {cls.Role.values}, got {role!r}"
            )

    def save(self, *args, **kwargs):
        self._validate_role(self.role)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Message({self.role}, session={self.session_id})"
