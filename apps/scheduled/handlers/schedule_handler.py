import logging
from datetime import timedelta

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
    RESPONSE_WINDOW_HOURS = 1

    def handle(self, user: User) -> None:
        """
        Celery beat entry point for a scheduled prompt cycle.
        Closes any stale scheduled session before dispatching a new prompt.
        """
        if not user.is_opted_in:
            logger.debug("Skipping user %s — not opted in", user.id)
            return

        if user.chat_mode != ChatMode.SCHEDULED:
            logger.debug("Skipping user %s — not in scheduled mode", user.id)
            return

        if self.notification_service.is_dnd_active(user):
            logger.debug("Skipping user %s — DND active", user.id)
            return

        Session.close_all_open(user, chat_mode=ChatMode.SCHEDULED)

        session = self.open_session(user, chat_mode=ChatMode.SCHEDULED)
        self.dispatch(user, session, self.PROMPT_TEMPLATE_KEY)
        logger.info("Prompt dispatched to user %s (session %s)", user.id, session.id)

    def handle_inbound(self, user: User, content: str) -> None:
        """
        Handle an inbound response to a scheduled prompt.
        Records the message, generates a reply, and keeps the session
        open until the LLM signals the conversation is complete.
        """
        session = self._get_open_session(user)
        if session is None:
            logger.warning(
                "Received response from user %s but no open session found", user.id
            )
            return

        self.write_message(session, role=Message.Role.USER, content=content)

        if self.llm_service:
            result = self.llm_service.generate(session=session)
            self.write_message(
                session,
                role=Message.Role.BOT,
                content=result.message,
                metadata={"categories_covered": result.categories_covered},
            )
            self.notification_service.send_reply(user, text=result.message)

            if result.conversation_complete:
                self.close_session(session)
                logger.info(
                    "Session %s closed for user %s", session.id, user.id
                )
            else:
                logger.info(
                    "Session %s still active for user %s", session.id, user.id
                )
        else:
            self.close_session(session)
            logger.info(
                "Session %s closed (no LLM) for user %s", session.id, user.id
            )

    @classmethod
    def expire_stale_sessions(cls) -> None:
        """
        Close any scheduled sessions that have exceeded the response window.
        Called periodically by a Celery task.
        """
        cutoff = timezone.now() - timedelta(hours=cls.RESPONSE_WINDOW_HOURS)
        stale = Session.objects.filter(
            chat_mode=ChatMode.SCHEDULED,
            status__in=[Session.Status.ACTIVE, Session.Status.AWAITING_RESPONSE],
            updated_at__lt=cutoff,
        )
        count = stale.count()
        stale.update(status=Session.Status.CLOSED)
        logger.info("Expired %s stale scheduled session(s)", count)

    def _get_open_session(self, user: User) -> Session | None:
        return Session.objects.filter(
            user=user,
            chat_mode=ChatMode.SCHEDULED,
            status__in=[Session.Status.ACTIVE, Session.Status.AWAITING_RESPONSE],
        ).first()
