import logging
from pathlib import Path

from django.conf import settings
from openai import APIError, OpenAI

from apps.core.models import Message, Session
from apps.core.services import LLMService

logger = logging.getLogger(__name__)

ROLE_MAP = {
    Message.Role.USER: "user",
    Message.Role.BOT: "assistant",
}

SYSTEM_PROMPT_PATH = Path(settings.BASE_DIR) / "templates" / "llm" / "system_prompt.txt"


class OpenAILLMService(LLMService):
    """
    OpenAI implementation of LLMService.
    Uses the Chat Completions API to generate responses.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT_PATH.read_text().strip()

    def generate(self, session: Session, user_message: str) -> str:
        messages = self._build_messages(session, user_message)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content
        except APIError as e:
            logger.error(
                "OpenAI API error for session %s: %s", session.id, e,
            )
            raise

    def _build_messages(self, session: Session, user_message: str) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]

        for msg in session.messages.order_by("created_at"):
            role = ROLE_MAP.get(msg.role)
            if role:
                messages.append({"role": role, "content": msg.content})

        messages.append({"role": "user", "content": user_message})
        return messages
