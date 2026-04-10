import logging
from datetime import datetime, timedelta
from typing import override
from zoneinfo import ZoneInfo

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
    PROMPT_INTERVAL_HOURS = 2
    SCHEDULE_START_HOUR = 7
    SCHEDULE_END_HOUR = 19

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
                session.mark_awaiting()

    def is_within_schedule(self, user: User) -> bool:
        """
        Check whether the current time in the user's local timezone
        falls within their schedule window [start, end).
        """
        tz_name = self.notification_service.resolve_timezone(user)
        overrides = self.notification_service.resolve_schedule(user)
        start = overrides.get("schedule_start", self.SCHEDULE_START_HOUR)
        end = overrides.get("schedule_end", self.SCHEDULE_END_HOUR)
        user_hour = datetime.now(ZoneInfo(tz_name)).hour

        if start <= end:
            return start <= user_hour < end

        return user_hour >= start or user_hour < end

    def is_dnd_blocked(self, user: User) -> bool:
        """
        Check whether the user should be blocked from receiving a prompt
        due to Do Not Disturb. Returns False (not blocked) if the user
        has opted out of DND respect.
        """
        if not user.respect_dnd:
            return False
        return self.notification_service.is_dnd_active(user)

    def dispatch_scheduled_prompt(self, user: User) -> None:
        """
        Celery beat entry point for a scheduled prompt cycle.
        Checks delivery rules, then closes any stale scheduled session
        before dispatching a new prompt.
        """
        if self.is_dnd_blocked(user):
            return

        if not self.is_within_schedule(user):
            return

        Session.close_all_open(user, chat_mode=ChatMode.SCHEDULED)

        session = Session.open(user, chat_mode=ChatMode.SCHEDULED)
        self.dispatch(user, session, self.PROMPT_TEMPLATE_KEY)

    @classmethod
    def expire_stale_sessions(cls) -> None:
        """
        Close any scheduled sessions that have exceeded the prompt interval.
        Called periodically by a Celery task.
        """
        cutoff = timezone.now() - timedelta(hours=cls.PROMPT_INTERVAL_HOURS)
        count = Session.close_all_open(
            chat_mode=ChatMode.SCHEDULED,
            stale_before=cutoff,
        )
        logger.info("Expired %s stale scheduled session(s)", count)
