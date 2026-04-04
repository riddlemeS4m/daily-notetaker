from django.db import models


class ChatMode(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    CONVERSATIONAL = "conversational", "Conversational"
