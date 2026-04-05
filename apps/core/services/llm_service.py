from abc import ABC, abstractmethod

from apps.core.models import Session


class LLMService(ABC):
    """
    Abstract base class for all LLM vendor integrations.
    Concrete implementations handle vendor-specific API details.
    """

    @abstractmethod
    def generate(self, session: Session, user_message: str) -> str:
        """
        Generate a reply given the current session and latest user message.

        Implementations should build conversation history from
        session.messages and call the underlying LLM API.

        Args:
            session: The active Session (provides message history).
            user_message: The latest inbound message from the user.

        Returns:
            The generated reply text.
        """
        raise NotImplementedError
