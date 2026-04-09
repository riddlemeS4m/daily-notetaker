import json
from pathlib import Path
from typing import override

from django.conf import settings
from openai import OpenAI

from apps.core.models import Message, Session
from apps.core.services import LLMService

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

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT_PATH.read_text().strip()

    @override
    def generate(self, session: Session) -> LLMService.GenerateResult:
        messages = self._build_messages(session)
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

    def _build_messages(self, session: Session) -> list[dict]:
        messages = [{"role": "system", "content": self.system_prompt}]

        for message in session.messages.order_by("created_at"):
            role = ROLE_MAP.get(message.role)
            if role:
                messages.append({"role": role, "content": message.content})

        return messages
