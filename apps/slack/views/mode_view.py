from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.core.models import Session
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
class ModeView(View):
    """
    Handles the /mode [mode] slash command.
    With no argument, returns the user's current mode.
    With an argument, switches the user's chat_mode preference.
    """

    def post(self, request, *args, **kwargs):
        user = request.slack_integration.user
        text = request.slack_text

        if not text:
            return JsonTemplateLoader.ephemeral_response(
                "commands/mode/current_mode.json", mode=user.chat_mode
            )

        mode = ChatMode.parse(text)
        if mode is None:
            raise SlackCommandError("commands/mode/invalid_mode.json")

        old_mode = user.switch_mode(mode)
        Session.close_all_open(user, chat_mode=old_mode)

        return JsonTemplateLoader.ephemeral_response(
            "commands/mode/success.json", mode=mode
        )
