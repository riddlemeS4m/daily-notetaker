import logging

from apps.core.constants import ChatMode
from apps.core.handlers import SessionHandler
from apps.core.models import Message, Session
from apps.users.models import User

logger = logging.getLogger(__name__)


class ConversationHandler(SessionHandler):
    """
    Handles conversational sessions.
    Pull-initiated: triggered by an inbound message from the user.
    Sessions remain open across turns until explicitly closed.
    """

    CHAT_MODE = ChatMode.CONVERSATIONAL

    def handle_inbound(self, user: User, content: str) -> None:
        """
        Handle an inbound user message.
        Looks up or opens a session, records the message, generates
        and dispatches a reply. Closes the session when the LLM
        signals the conversation is complete.
        """
        if not user.is_opted_in:
            logger.debug("Ignoring message from user %s — not opted in", user.id)
            return

        if user.chat_mode != ChatMode.CONVERSATIONAL:
            logger.debug(
                "Ignoring message from user %s — not in conversational mode", user.id
            )
            return

        session = self._get_or_open_session(user)
        self.write_message(session, role=Message.Role.USER, content=content)

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
            "Conversational reply sent to user %s (session %s)", user.id, session.id
        )

    def _get_or_open_session(self, user: User) -> Session:
        session = Session.objects.filter(
            user=user,
            chat_mode=ChatMode.CONVERSATIONAL,
            status__in=[Session.Status.ACTIVE, Session.Status.AWAITING_RESPONSE],
        ).first()
        if session is None:
            session = self.open_session(user, chat_mode=ChatMode.CONVERSATIONAL)
        return session
