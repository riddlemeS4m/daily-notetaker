from django.db import models

from apps.core.models import Message
from apps.users.models import UserIntegration


class IntegrationJob(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    TERMINAL_STATUSES = frozenset({Status.SENT, Status.FAILED, Status.SKIPPED})

    integration = models.ForeignKey(
        UserIntegration,
        on_delete=models.CASCADE,
        related_name="jobs",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integration_jobs",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    scheduled_at = models.DateTimeField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "scheduled_at"],
                name="ix_job_status_scheduled_at",
            ),
        ]

    def mark_sent(self, message: Message | None = None) -> None:
        self.status = self.Status.SENT
        if message is not None:
            self.message = message
        self.save(update_fields=["status", "message", "updated_at"])

    def mark_failed(self, reason: str = "") -> None:
        self.status = self.Status.FAILED
        if reason:
            self.metadata["failure_reason"] = reason
        self.save(update_fields=["status", "metadata", "updated_at"])

    def mark_skipped(self, reason: str = "") -> None:
        self.status = self.Status.SKIPPED
        if reason:
            self.metadata["skip_reason"] = reason
        self.save(update_fields=["status", "metadata", "updated_at"])

    def __str__(self):
        return f"IntegrationJob({self.integration}, {self.status}, {self.scheduled_at})"
