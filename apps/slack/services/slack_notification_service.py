import time
from typing import Any, override

from slack_sdk import WebClient

from apps.core.services import JsonTemplateLoader, NotificationService
from apps.slack.models import SlackIntegration
from apps.users.models import User


class SlackNotificationService(NotificationService):
    """
    Slack implementation of NotificationService.
    Requires bot scopes: chat:write, users:read
    """

    VENDOR = "slack"
    FALLBACK_TEXT = "Got a minute? Time for a quick reflection."

    def __init__(self, token: str):
        self.client = WebClient(token=token)
        self._user_profile: dict[str, dict[str, Any]] = {}
        self._integration: dict[int, SlackIntegration] = {}

    def _get_integration(self, user: User) -> SlackIntegration:
        if user.pk not in self._integration:
            self._integration[user.pk] = SlackIntegration.for_user(user)
        return self._integration[user.pk]

    def _fetch_user(self, external_id: str) -> dict[str, Any]:
        if external_id not in self._user_profile:
            response = self.client.users_info(user=external_id)
            self._user_profile[external_id] = response["user"]
        return self._user_profile[external_id]

    @override
    def resolve_username(self, external_id: str) -> str:
        user = self._fetch_user(external_id)
        return user.get("name", external_id)

    @override
    def resolve_name(self, external_id: str) -> tuple[str, str]:
        profile = self._fetch_user(external_id).get("profile", {})
        return profile.get("first_name", ""), profile.get("last_name", "")

    @override
    def resolve_context(self, user: User) -> dict[str, Any]:
        integration = self._get_integration(user)
        return {
            "channel": integration.slack_user_id,
        }

    @override
    def send_prompt(self, user: User, template_key: str) -> None:
        """
        Send a templated Block Kit message to the user's Slack DM.
        """
        context = self.resolve_context(user)
        blocks = JsonTemplateLoader.load(template_key)
        self.client.chat_postMessage(
            channel=context["channel"],
            text=self.FALLBACK_TEXT,
            blocks=blocks,
        )

    @override
    def send_reply(self, user: User, text: str) -> None:
        """
        Send a plain-text message to the user's Slack DM.
        Used for dynamic content that doesn't come from a template.
        """
        context = self.resolve_context(user)
        self.client.chat_postMessage(
            channel=context["channel"],
            text=text,
        )

    @override
    def read_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a Slack Events API message payload into a normalised dict.

        Returns:
            {
                "external_id": str,   # Slack user ID
                "content": str,       # message text
            }
        """
        event = payload.get("event", {})
        return {
            "external_id": event.get("user"),
            "content": event.get("text", "").strip(),
        }

    @override
    def is_dnd_active(self, user: User) -> bool:
        integration = self._get_integration(user)
        resp = self.client.dnd_info(user=integration.slack_user_id)
        if resp.get("snooze_enabled", False):
            return True
        now = time.time()
        start = resp.get("next_dnd_start_ts", 0)
        end = resp.get("next_dnd_end_ts", 0)
        return start <= now < end

    @override
    def resolve_timezone(self, user: User) -> str:
        integration = self._get_integration(user)
        profile = self._fetch_user(integration.slack_user_id)
        return profile.get("tz", "UTC")

    @override
    def resolve_schedule(self, user: User) -> dict[str, Any]:
        return self._get_integration(user).schedule_overrides
