from abc import ABC, abstractmethod
from typing import Any

from apps.users.models import User


class NotificationService(ABC):
    """
    Abstract base class for all notification vendor integrations.
    Concrete implementations handle vendor-specific transport details.
    """

    @abstractmethod
    def resolve_username(self, external_id: str) -> str:
        """
        Return a human-readable username for the given vendor user.

        Used to populate ``User.username`` at account creation time
        so the field contains a recognisable handle rather than an
        opaque vendor ID.

        Args:
            external_id: The vendor-specific user identifier
                         (e.g. a Slack user ID).
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_name(self, external_id: str) -> tuple[str, str]:
        """
        Return ``(first_name, last_name)`` for the given vendor user.

        Used to populate ``User.first_name`` and ``User.last_name``
        at account creation time.

        Args:
            external_id: The vendor-specific user identifier
                         (e.g. a Slack user ID).
        """
        raise NotImplementedError

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

    @abstractmethod
    def is_dnd_active(self, user: User) -> bool:
        """
        Check whether the vendor indicates the user is currently in
        Do Not Disturb mode (scheduled or manual).
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_timezone(self, user: User) -> str:
        """
        Return the user's IANA timezone string (e.g. "America/New_York")
        as reported by the vendor. Should be fetched live — users may
        travel and change timezones between dispatch cycles.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_schedule(self, user: User) -> dict[str, Any]:
        """
        Return vendor-side schedule configuration overrides stored on
        the user's integration.

        Recognised keys (absent means "use application default"):
            - schedule_start: int  (hour 0-23)
            - schedule_end:   int  (hour 0-23)
        """
        raise NotImplementedError
