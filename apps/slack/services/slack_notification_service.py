import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from apps.core.services import MessageTemplate, NotificationService
from apps.slack.models import SlackIntegration
from apps.users.models import User

logger = logging.getLogger(__name__)


class SlackNotificationService(NotificationService):
    """
    Slack implementation of NotificationService.
    Requires bot scopes: chat:write, dnd:read
    """

    VENDOR = "slack"
    FALLBACK_TEXT = "You have a new check-in prompt."

    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def is_dnd_active(self, user: User) -> bool:
        """
        Check whether the user currently has Do Not Disturb active.
        Fails open — returns False if the API call fails, so the
        prompt is sent rather than silently dropped.
        """
        try:
            integration = SlackIntegration.for_user(user)
            resp = integration.get_dnd_status(self.client)
            return resp["dnd_enabled"] and resp["snooze_enabled"]
        except SlackApiError as e:
            logger.error("Failed to fetch DND status for user %s: %s", user.id, e)
            return False

    def resolve_context(self, user: User) -> dict:
        integration = SlackIntegration.for_user(user)
        return {
            "channel": integration.slack_user_id,
        }

    def send_prompt(self, user: User, template_key: str) -> None:
        """
        Send a templated Block Kit message to the user's Slack DM.
        """
        context = self.resolve_context(user)
        blocks = MessageTemplate.load(template_key)
        try:
            self.client.chat_postMessage(
                channel=context["channel"],
                text=self.FALLBACK_TEXT,
                blocks=blocks,
            )
        except SlackApiError as e:
            logger.error("Failed to send prompt to user %s via Slack: %s", user.id, e)
            raise

    def send_reply(self, user: User, text: str) -> None:
        """
        Send a plain-text message to the user's Slack DM.
        Used for dynamic content that doesn't come from a template.
        """
        context = self.resolve_context(user)
        try:
            self.client.chat_postMessage(
                channel=context["channel"],
                text=text,
            )
        except SlackApiError as e:
            logger.error("Failed to send reply to user %s via Slack: %s", user.id, e)
            raise

    def read_response(self, payload: dict) -> dict:
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
