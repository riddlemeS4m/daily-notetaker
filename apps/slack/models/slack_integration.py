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

    @staticmethod
    def _valid_hour(val: object) -> int | None:
        """Return val as a valid hour (0-23), or None if unusable."""
        try:
            hour = int(val)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return hour if 0 <= hour <= 23 else None

    @property
    def schedule_start(self) -> int | None:
        val = self.metadata.get("schedule_start")
        return self._valid_hour(val) if val is not None else None

    @property
    def schedule_end(self) -> int | None:
        val = self.metadata.get("schedule_end")
        return self._valid_hour(val) if val is not None else None

    def _set_schedule_hour(self, key: str, hour: int) -> None:
        if self._valid_hour(hour) is None:
            raise ValueError(f"Hour must be an integer 0-23, got {hour!r}")
        self.metadata[key] = hour
        self.save(update_fields=["metadata", "updated_at"])

    def set_schedule_start(self, hour: int) -> None:
        self._set_schedule_hour("schedule_start", hour)

    def set_schedule_end(self, hour: int) -> None:
        self._set_schedule_hour("schedule_end", hour)

    @property
    def schedule_overrides(self) -> dict[str, int]:
        result: dict[str, int] = {}
        if self.schedule_start is not None:
            result["schedule_start"] = self.schedule_start
        if self.schedule_end is not None:
            result["schedule_end"] = self.schedule_end
        return result

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
        cls,
        slack_user_id: str,
        *,
        username: str,
        first_name: str,
        last_name: str,
        metadata: dict[str, Any] | None = None,
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
                    user = User.objects.create(
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                    )
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
