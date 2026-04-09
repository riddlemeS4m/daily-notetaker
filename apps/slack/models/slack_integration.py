from __future__ import annotations

from typing import Any

from django.db import IntegrityError, transaction

from apps.users.models import User, UserIntegration


class SlackIntegration(UserIntegration):
    """
    Proxy model for Slack-specific UserIntegration instances.
    Shares the UserIntegration table — no migration needed.
    Adds Slack-aware properties and methods to keep Slack logic
    out of SlackNotificationService where possible.
    """

    VENDOR = "slack"

    class Meta:
        proxy = True

    @property
    def slack_user_id(self) -> str:
        return self.external_id

    @property
    def team_id(self) -> str | None:
        return self.metadata.get("team_id")

    @classmethod
    def for_user(cls, user: User) -> SlackIntegration:
        """Fetch the SlackIntegration for a given User, or raise DoesNotExist."""
        return cls.objects.get(user=user, vendor=cls.VENDOR)

    @classmethod
    def for_external_id(cls, slack_user_id: str) -> SlackIntegration:
        """Fetch the SlackIntegration by Slack user ID, or raise DoesNotExist."""
        return cls.objects.select_related("user").get(
            vendor=cls.VENDOR,
            external_id=slack_user_id,
        )

    @classmethod
    def find_or_create(
        cls, slack_user_id: str, metadata: dict[str, Any] | None = None,
    ) -> SlackIntegration:
        """
        Return the SlackIntegration for the given Slack user ID,
        creating a new User and SlackIntegration if none exists.
        """
        try:
            return cls.for_external_id(slack_user_id)
        except cls.DoesNotExist:
            try:
                with transaction.atomic():
                    user = User.objects.create(username=slack_user_id)
                    return cls.objects.create(
                        user=user,
                        vendor=cls.VENDOR,
                        external_id=slack_user_id,
                        metadata=metadata or {},
                    )
            except IntegrityError:
                return cls.for_external_id(slack_user_id)

    @classmethod
    def get_user(cls, slack_user_id: str) -> User | None:
        """Resolve a Slack user ID to a Django User, or return None."""
        try:
            return cls.for_external_id(slack_user_id).user
        except cls.DoesNotExist:
            return None
