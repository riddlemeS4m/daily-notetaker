from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from apps.core.models import Session


class LLMService(ABC):
    """
    Abstract base class for all LLM vendor integrations.
    Concrete implementations handle vendor-specific API details.
    """

    @dataclass
    class GenerateResult:
        message: str
        categories_covered: list[str] = field(default_factory=list)
        conversation_complete: bool = False

    @abstractmethod
    def generate(self, session: Session) -> GenerateResult:
        """
        Generate a reply given the current session.

        Implementations should build conversation history from
        session.messages and call the underlying LLM API.

        Args:
            session: The active Session (provides message history).

        Returns:
            A GenerateResult containing the reply and structured metadata.
        """
        raise NotImplementedError
