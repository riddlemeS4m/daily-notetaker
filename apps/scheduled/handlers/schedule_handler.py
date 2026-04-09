import logging
from datetime import timedelta
from typing import override

from django.conf import settings
from django.utils import timezone

from apps.core.constants import ChatMode
from apps.core.handlers import SessionHandler
from apps.core.models import Message, Session
from apps.users.models import User

logger = logging.getLogger(__name__)


class ScheduleHandler(SessionHandler):
    """
    Handles scheduled prompt sessions.
    Called by Celery beat on a fixed interval for each opted-in user.
    """

    CHAT_MODE = ChatMode.SCHEDULED
    PROMPT_TEMPLATE_KEY = "scheduled/hourly_prompt.json"

    @override
    def handle_inbound(self, user: User, content: str) -> None:
        """
        Handle an inbound response to a scheduled prompt.
        Records the message, generates a reply, and keeps the session
        open until the LLM signals the conversation is complete.
        """
        session = Session.get_open(user, chat_mode=ChatMode.SCHEDULED)
        if session is None:
            return  # TODO: consider using find_or_create instead of returning

        session.add_message(role=Message.Role.USER, content=content)

        if self.llm_service:
            result = self.generate_and_reply(user, session)
            if result.conversation_complete:
                session.close()
        else:
            session.close()

    def dispatch_scheduled_prompt(self, user: User) -> None:
        """
        Celery beat entry point for a scheduled prompt cycle.
        Closes any stale scheduled session before dispatching a new prompt.
        """
        Session.close_all_open(user, chat_mode=ChatMode.SCHEDULED)

        session = Session.open(user, chat_mode=ChatMode.SCHEDULED)
        self.dispatch(user, session, self.PROMPT_TEMPLATE_KEY)

    @classmethod
    def expire_stale_sessions(cls) -> None:
        """
        Close any scheduled sessions that have exceeded the prompt interval.
        Called periodically by a Celery task.
        """
        cutoff = timezone.now() - timedelta(hours=settings.PROMPT_INTERVAL_HOURS)
        count = Session.close_all_open(
            chat_mode=ChatMode.SCHEDULED, stale_before=cutoff,
        )
        logger.info("Expired %s stale scheduled session(s)", count)
