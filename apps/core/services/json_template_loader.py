import json
from pathlib import Path
from string import Template
from typing import Any

from django.conf import settings
from django.http import JsonResponse


class JsonTemplateLoader:
    """
    Loads JSON templates from flat files at runtime.
    Templates live under BASE_DIR/templates/slack/.
    """

    BASE_DIR = Path(settings.BASE_DIR) / "templates" / "slack"

    @classmethod
    def load(cls, template_key: str, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Load and return a parsed Block Kit blocks array.

        Args:
            template_key: Relative path from templates/slack/,
                          e.g. "scheduled/hourly_prompt.json".
            **kwargs:     Values to substitute for $var placeholders.

        Raises:
            FileNotFoundError: If the template file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        path = cls.BASE_DIR / template_key
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")
        raw = path.read_text()
        if kwargs:
            raw = Template(raw).safe_substitute(**kwargs)
        return json.loads(raw)

    @classmethod
    def ephemeral_response(cls, template_key: str, **kwargs) -> JsonResponse:
        blocks = cls.load(template_key, **kwargs)
        return JsonResponse({
            "response_type": "ephemeral",
            "blocks": blocks,
            "text": cls.text(blocks),
        })

    @staticmethod
    def text(blocks: list[dict[str, Any]]) -> str:
        """Extract the plain text from the first section block."""
        for block in blocks:
            if block["type"] == "section" and "text" in block:
                return block["text"]["text"]
        return ""
