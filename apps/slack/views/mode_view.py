import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.slack.models import SlackIntegration

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ModeView(View):
    """
    Handles the /mode [mode] slash command.
    With no argument, returns the user's current mode.
    With an argument, switches the user's chat_mode preference.
    """

    def post(self, request, *args, **kwargs):
        slack_user_id = request.POST.get("user_id")

        user = SlackIntegration.get_user(slack_user_id)
        if user is None or not user.is_opted_in:
            return JsonResponse(
                {
                    "response_type": "ephemeral",
                    "text": "You need to opt-in first. Use `/activate <mode>` to get started.",
                }
            )

        text = request.POST.get("text", "").strip()
        if not text:
            return JsonResponse(
                {
                    "response_type": "ephemeral",
                    "text": f"Your current mode is *{user.chat_mode}*.",
                }
            )

        mode = ChatMode.parse(text)
        if mode is None:
            return JsonResponse(
                {
                    "response_type": "ephemeral",
                    "text": "Please specify a mode: `/mode scheduled` or `/mode conversational`",
                }
            )

        user.chat_mode = mode
        user.save(update_fields=["chat_mode", "updated_at"])

        return JsonResponse(
            {
                "response_type": "ephemeral",
                "text": f"Switched to *{mode}* mode.",
            }
        )
