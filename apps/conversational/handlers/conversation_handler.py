from typing import override

from apps.core.constants import ChatMode
from apps.core.handlers import SessionHandler
from apps.core.models import Message, Session
from apps.users.models import User


class ConversationHandler(SessionHandler):
    """
    Handles conversational sessions.
    Pull-initiated: triggered by an inbound message from the user.
    Sessions remain open across turns until explicitly closed.
    """

    CHAT_MODE = ChatMode.CONVERSATIONAL

    @override
    def handle_inbound(self, user: User, content: str) -> None:
        """
        Handle an inbound user message.
        Looks up or opens a session, records the message, generates
        and dispatches a reply. Closes the session when the LLM
        signals the conversation is complete.
        """
        session = Session.find_or_create(user, chat_mode=ChatMode.CONVERSATIONAL)
        session.add_message(role=Message.Role.USER, content=content)

        result = self.generate_and_reply(user, session)

        if result.conversation_complete:
            session.close()
