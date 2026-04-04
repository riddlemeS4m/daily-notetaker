from apps.users.models import UserIntegration


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

    def get_dnd_status(self, client) -> dict:
        """
        Fetch DND info from the Slack API for this user.
        Returns the full dnd_info response dict.
        Caller is responsible for handling SlackApiError.
        """
        return client.dnd_info(user=self.slack_user_id)

    @classmethod
    def for_user(cls, user):
        """Fetch the SlackIntegration for a given User, or raise DoesNotExist."""
        return cls.objects.get(user=user, vendor=cls.VENDOR)

    @classmethod
    def for_external_id(cls, slack_user_id: str):
        """Fetch the SlackIntegration by Slack user ID, or raise DoesNotExist."""
        return cls.objects.select_related("user").get(
            vendor=cls.VENDOR,
            external_id=slack_user_id,
        )

    @classmethod
    def get_user(cls, slack_user_id: str):
        """Resolve a Slack user ID to a Django User, or return None."""
        try:
            return cls.for_external_id(slack_user_id).user
        except cls.DoesNotExist:
            return None
