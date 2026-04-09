from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.services import JsonTemplateLoader
from apps.slack.decorators import (
    require_opted_in,
    require_slack_integration,
    verify_slack_signature,
)
from apps.slack.exceptions import SlackCommandError


@method_decorator(
    [csrf_exempt, verify_slack_signature, require_slack_integration, require_opted_in],
    name="dispatch",
)
class DndView(View):
    """
    Handles the /dnd [on|off] slash command.
    Toggles or explicitly sets whether the app respects vendor DND
    when dispatching scheduled prompts to this user.
    """

    VALID_VALUES = {"on", "off"}

    def post(self, request, *args, **kwargs):
        user = request.slack_integration.user
        text = request.slack_text.lower()

        if text and text not in self.VALID_VALUES:
            raise SlackCommandError("commands/dnd/invalid_value.json")

        if not text:
            text = "off" if user.respect_dnd else "on"

        user.set_dnd(text)

        return JsonTemplateLoader.ephemeral_response(
            "commands/dnd/success.json", value=text
        )
