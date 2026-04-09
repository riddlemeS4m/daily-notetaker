from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.core.models import Session
from apps.core.services import JsonTemplateLoader
from apps.slack.decorators import require_slack_integration, verify_slack_signature

@method_decorator(
    [csrf_exempt, verify_slack_signature, require_slack_integration],
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

        if not user.is_opted_in:
            return JsonTemplateLoader.ephemeral_response(
                "commands/mode/not_opted_in.json"
            )

        text = request.POST.get("text", "").strip()
        if not text:
            return JsonTemplateLoader.ephemeral_response(
                "commands/mode/current_mode.json", mode=user.chat_mode
            )

        mode = ChatMode.parse(text)
        if mode is None:
            return JsonTemplateLoader.ephemeral_response(
                "commands/mode/invalid_mode.json"
            )

        old_mode = user.switch_mode(mode)
        Session.close_all_open(user, chat_mode=old_mode)

        return JsonTemplateLoader.ephemeral_response(
            "commands/mode/success.json", mode=mode
        )
