from abc import ABC, abstractmethod


class NotificationService(ABC):
    """
    Abstract base class for all notification vendor integrations.
    Concrete implementations handle vendor-specific transport details.
    """

    @abstractmethod
    def send_prompt(self, user, template_key: str) -> None:
        """
        Send a bot-initiated prompt to a user, rendered from a template.

        Args:
            user: The User instance to notify.
            template_key: Relative path to the flat-file message template,
                          e.g. "scheduled/hourly_prompt.json".
        """
        raise NotImplementedError

    @abstractmethod
    def send_reply(self, user, text: str) -> None:
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
    def read_response(self, payload: dict) -> dict:
        """
        Parse an inbound vendor payload into a normalised response dict.

        Returns a dict with at minimum:
            {
                "external_id": str,   # vendor user identifier
                "content": str,       # message text
            }
        """
        raise NotImplementedError
