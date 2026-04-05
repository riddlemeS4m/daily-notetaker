import json
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

    def generate(self, session: Session) -> LLMService.GenerateResult:
        messages = self._build_messages(session)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw = json.loads(response.choices[0].message.content)
            return self.GenerateResult(
                message=raw["message"],
                categories_covered=raw.get("categories_covered", []),
                conversation_complete=raw.get("conversation_complete", False),
            )
        except APIError as e:
            logger.error(
                "OpenAI API error for session %s: %s", session.id, e,
            )
            raise

    def _build_messages(self, session: Session) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]

        for msg in session.messages.order_by("created_at"):
            role = ROLE_MAP.get(msg.role)
            if role:
                messages.append({"role": role, "content": msg.content})

        return messages
