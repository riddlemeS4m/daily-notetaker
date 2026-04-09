from typing import Any, override

from slack_sdk import WebClient

from apps.core.services import JsonTemplateLoader, NotificationService
from apps.slack.models import SlackIntegration
from apps.users.models import User


class SlackNotificationService(NotificationService):
    """
    Slack implementation of NotificationService.
    Requires bot scopes: chat:write
    """

    VENDOR = "slack"
    FALLBACK_TEXT = "Got a minute? Time for a quick reflection."

    def __init__(self, token: str):
        self.client = WebClient(token=token)

    @override
    def resolve_context(self, user: User) -> dict[str, Any]:
        integration = SlackIntegration.for_user(user)
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
