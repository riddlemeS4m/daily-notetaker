import logging

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.slack.models import SlackIntegration

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class DeactivateView(View):
    """
    Handles the /deactivate slash command.
    Sets opted_out_at on the User, stopping further prompts.
    """

    def post(self, request, *args, **kwargs):
        slack_user_id = request.POST.get("user_id")

        user = SlackIntegration.get_user(slack_user_id)
        if user is None or not user.is_opted_in:
            return JsonResponse(
                {
                    "response_type": "ephemeral",
                    "text": "You don't have an active check-in session.",
                }
            )

        user.opted_out_at = timezone.now()
        user.save(update_fields=["opted_out_at", "updated_at"])

        return JsonResponse(
            {
                "response_type": "ephemeral",
                "text": "Check-ins paused. Use `/activate <mode>` to resume.",
            }
        )
