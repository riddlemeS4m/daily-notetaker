import logging

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.slack.models import SlackIntegration
from apps.users.models import User

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ActivateView(View):
    """
    Handles the /activate <mode> slash command.
    Creates a User + SlackIntegration if they don't exist, sets mode and opt-in.
    """

    def post(self, request, *args, **kwargs):
        slack_user_id = request.POST.get("user_id")
        team_id = request.POST.get("team_id")
        text = request.POST.get("text", "").strip().lower()

        if text not in ChatMode.values:
            return JsonResponse(
                {
                    "response_type": "ephemeral",
                    "text": "Please specify a mode: `/activate scheduled` or `/activate conversational`",
                }
            )

        try:
            integration = SlackIntegration.for_external_id(slack_user_id)
            user = integration.user
        except SlackIntegration.DoesNotExist:
            user = User.objects.create(username=slack_user_id)
            SlackIntegration.objects.create(
                user=user,
                vendor=SlackIntegration.VENDOR,
                external_id=slack_user_id,
                metadata={"team_id": team_id},
            )

        user.chat_mode = text
        user.opted_in_at = timezone.now()
        user.opted_out_at = None
        user.save(
            update_fields=["chat_mode", "opted_in_at", "opted_out_at", "updated_at"]
        )

        return JsonResponse(
            {
                "response_type": "ephemeral",
                "text": f"You're all set! Check-ins are active in *{text}* mode.",
            }
        )
