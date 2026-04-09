from __future__ import annotations

from abc import ABC, abstractmethod

from apps.core.exceptions import ApplicationError
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

    def __init__(
        self,
        notification_service: NotificationService,
        llm_service: LLMService | None = None,
    ):
        self.notification_service = notification_service
        self.llm_service = llm_service

    @classmethod
    def for_mode(cls, chat_mode: str, **kwargs) -> SessionHandler:
        """Resolve and instantiate the handler registered for chat_mode."""
        handler_cls = cls._registry.get(chat_mode)
        if handler_cls is None:
            raise ApplicationError(f"No handler registered for chat mode: {chat_mode}")
        return handler_cls(**kwargs)

    def dispatch(self, user: User, session: Session, template_key: str) -> None:
        """
        Send a prompt via the notification service and record the
        outbound message. Sets session status to awaiting_response.
        """
        self.notification_service.send_prompt(user, template_key)
        session.add_message(
            role=Message.Role.BOT,
            content=template_key,
            template_key=template_key,
        )
        session.mark_awaiting()

    def generate_and_reply(
        self, user: User, session: Session,
    ) -> LLMService.GenerateResult:
        """
        Run the LLM, persist its reply as a bot message, and send it
        to the user via the notification service.
        """
        if self.llm_service is None:
            # TODO: llm service should probably be always required
            raise ApplicationError("LLM service is required but was not provided")
        result = self.llm_service.generate(session=session)
        session.add_message(
            role=Message.Role.BOT,
            content=result.message,
            metadata={"categories_covered": result.categories_covered},
        )
        self.notification_service.send_reply(user, result.message)
        return result

    @abstractmethod
    def handle_inbound(self, user: User, content: str) -> None:
        """
        Handle an inbound message from a user.
        Uniform entry point called by views for all modes.
        """
        raise NotImplementedError
