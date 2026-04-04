from django.db import models

from .user import User


class UserIntegration(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    vendor = models.CharField(max_length=50)  # e.g. "slack"
    external_id = models.CharField(max_length=255)  # e.g. slack user id
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "external_id"],
                name="unique_vendor_external_id",
            )
        ]

    def __str__(self):
        return f"{self.vendor}:{self.external_id}"
