import logging

from celery import shared_task
from django.conf import settings

from apps.core.constants import ChatMode
from apps.scheduled.handlers import ScheduleHandler
from apps.slack.services import SlackNotificationService
from apps.users.models import User

logger = logging.getLogger(__name__)


@shared_task
def dispatch_scheduled_prompts():
    """
    Fetch all opted-in scheduled-mode users and dispatch a prompt to each.
    Skips users on DND or with an existing open session (handled in ScheduleHandler).
    """
    service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
    handler = ScheduleHandler(notification_service=service)

    users = User.objects.filter(
        chat_mode=ChatMode.SCHEDULED,
        opted_in_at__isnull=False,
        opted_out_at__isnull=True,
    )
    for user in users:
        try:
            handler.handle(user)
        except Exception as e:
            logger.error("Error dispatching prompt for user %s: %s", user.id, e)


@shared_task
def expire_stale_sessions():
    """
    Close scheduled sessions that have exceeded the response window.
    """
    try:
        ScheduleHandler.expire_stale_sessions()
    except Exception as e:
        logger.error("Error expiring stale sessions: %s", e)
