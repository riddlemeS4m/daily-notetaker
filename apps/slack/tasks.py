import logging

from celery import shared_task
from django.conf import settings

from apps.core.handlers import SessionHandler
from apps.openai.services import OpenAILLMService
from apps.slack.services import SlackNotificationService

logger = logging.getLogger(__name__)


@shared_task
def handle_slack_message(chat_mode: str, slack_user_id: str, content: str):
    """
    Process an inbound Slack message asynchronously so the event view
    can return 200 within Slack's 3-second timeout window.
    """
    from apps.slack.models import SlackIntegration

    user = SlackIntegration.get_user(slack_user_id)
    if user is None or not user.is_opted_in or not user.chat_mode:
        logger.debug("Skipping task for slack user %s — ineligible", slack_user_id)
        return

    notification_service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
    llm_service = OpenAILLMService(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
    )

    handler = SessionHandler.for_mode(
        chat_mode,
        notification_service=notification_service,
        llm_service=llm_service,
    )

    try:
        handler.handle_inbound(user=user, content=content)
    except Exception:
        logger.exception(
            "Error handling inbound message for slack user %s", slack_user_id
        )
        raise
