import logging

from apps.core.models import Session

logger = logging.getLogger(__name__)


class LLMService:
    """
    Stub for future LLM API integration.
    Returns a placeholder reply until wired to an external API.
    """

    def generate(self, session: Session, user_message: str) -> str:
        """
        Generate a reply given the current session and latest user message.
        In future: builds message history from session.messages.all()
        and calls an LLM API.
        """
        logger.debug("LLMService.generate called (stub) for session %s", session.id)
        return "Got it — I've recorded your update."
