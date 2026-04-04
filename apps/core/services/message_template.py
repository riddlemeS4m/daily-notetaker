import json
from pathlib import Path

from django.conf import settings


class MessageTemplate:
    """
    Loads Slack Block Kit JSON templates from flat files at runtime.
    Templates live under BASE_DIR/templates/slack/.
    """

    BASE_DIR = Path(settings.BASE_DIR) / "templates" / "slack"

    @classmethod
    def load(cls, template_key: str) -> dict:
        """
        Load and return a parsed template dict.

        Args:
            template_key: Relative path from templates/slack/,
                          e.g. "scheduled/hourly_prompt.json".

        Raises:
            FileNotFoundError: If the template file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        path = cls.BASE_DIR / template_key
        if not path.exists():
            raise FileNotFoundError(f"Message template not found: {path}")
        with path.open() as f:
            return json.load(f)
