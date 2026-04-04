from django.db import models


class ChatMode(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    CONVERSATIONAL = "conversational", "Conversational"

    @classmethod
    def parse(cls, text: str) -> str | None:
        cleaned = text.strip().lower()
        return cleaned if cleaned in cls.values else None
