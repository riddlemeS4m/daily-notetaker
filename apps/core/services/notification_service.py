from abc import ABC, abstractmethod
from typing import Any

from apps.users.models import User


class NotificationService(ABC):
    """
    Abstract base class for all notification vendor integrations.
    Concrete implementations handle vendor-specific transport details.
    """

    @abstractmethod
    def resolve_context(self, user: User) -> dict[str, Any]:
        """
        Resolve the delivery context for a user.

        Returns a dict of vendor-specific delivery parameters needed to
        reach the user in the correct context. At minimum includes the
        target address (e.g. channel, email, etc.).

        Today every implementation returns a single-context default.
        When multi-context support lands, this method will accept
        additional arguments to select the right context.
        """
        raise NotImplementedError

    @abstractmethod
    def send_prompt(self, user: User, template_key: str) -> None:
        """
        Send a bot-initiated prompt to a user, rendered from a template.

        Args:
            user: The User instance to notify.
            template_key: Relative path to the flat-file message template,
                          e.g. "scheduled/hourly_prompt.json".
        """
        raise NotImplementedError

    @abstractmethod
    def send_reply(self, user: User, text: str) -> None:
        """
        Send a plain-text reply to a user.
        Used for dynamic content (e.g. LLM-generated responses) that
        does not come from a template.

        Args:
            user: The User instance to notify.
            text: The message body to send.
        """
        raise NotImplementedError

    @abstractmethod
    def read_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Parse an inbound vendor payload into a normalised response dict.

        Returns a dict with at minimum:
            {
                "external_id": str,   # vendor user identifier
                "content": str,       # message text
            }
        """
        raise NotImplementedError
