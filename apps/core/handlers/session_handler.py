from __future__ import annotations

from abc import ABC, abstractmethod

from apps.core.models import Message, Session
from apps.core.services import LLMService, NotificationService
from apps.users.models import User


class SessionHandler(ABC):
    """
    Abstract base class for interaction mode handlers.
    Defines the session lifecycle contract shared across all modes.

    Concrete handlers declare a CHAT_MODE class attribute and are
    auto-registered via __init_subclass__. Use for_mode() to resolve
    and instantiate the correct handler for a given chat mode.
    """

    _registry: dict[str, type[SessionHandler]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        chat_mode = getattr(cls, "CHAT_MODE", None)
        if chat_mode is not None:
            SessionHandler._registry[chat_mode] = cls

    @classmethod
    def for_mode(cls, chat_mode: str, **kwargs) -> SessionHandler:
        """Resolve and instantiate the handler registered for chat_mode."""
        handler_cls = cls._registry.get(chat_mode)
        if handler_cls is None:
            raise ValueError(f"No handler registered for chat mode: {chat_mode}")
        return handler_cls(**kwargs)

    def __init__(
        self,
        notification_service: NotificationService,
        llm_service: LLMService = None,
    ):
        self.notification_service = notification_service
        self.llm_service = llm_service

    def open_session(self, user: User, chat_mode: str) -> Session:
        """Create and persist a new Session for the user."""
        return Session.objects.create(
            user=user,
            chat_mode=chat_mode,
            status=Session.Status.ACTIVE,
        )

    def close_session(self, session: Session) -> None:
        """Mark a Session as closed."""
        session.status = Session.Status.CLOSED
        session.save(update_fields=["status", "updated_at"])

    def write_message(
        self,
        session: Session,
        role: str,
        content: str,
        template_key: str = None,
        metadata: dict = None,
    ) -> Message:
        """Persist a Message to the given Session."""
        return Message.objects.create(
            session=session,
            role=role,
            content=content,
            template_key=template_key,
            metadata=metadata or {},
        )

    def dispatch(self, user: User, session: Session, template_key: str) -> None:
        """
        Send a prompt via the notification service and record the
        outbound message. Sets session status to awaiting_response.
        """
        self.notification_service.send_prompt(user, template_key)
        self.write_message(
            session,
            role=Message.Role.BOT,
            content=template_key,
            template_key=template_key,
        )
        session.status = Session.Status.AWAITING_RESPONSE
        session.save(update_fields=["status", "updated_at"])

    @abstractmethod
    def handle_inbound(self, user: User, content: str) -> None:
        """
        Handle an inbound message from a user.
        Uniform entry point called by views for all modes.
        """
        raise NotImplementedError
