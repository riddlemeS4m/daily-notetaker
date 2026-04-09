from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.core.models import Session
from apps.core.services import JsonTemplateLoader
from apps.slack.decorators import verify_slack_signature
from apps.slack.exceptions import SlackCommandError
from apps.slack.models import SlackIntegration
from apps.slack.services import SlackNotificationService


@method_decorator([csrf_exempt, verify_slack_signature], name="dispatch")
class ActivateView(View):
    """
    Handles the /activate <mode> slash command.
    Creates a User + SlackIntegration if they don't exist, sets mode and opt-in.
    """

    def post(self, request, *args, **kwargs):
        slack_user_id = request.POST.get("user_id")
        team_id = request.POST.get("team_id")
        text = request.POST.get("text", "").strip()
        mode = ChatMode.parse(text) if text else ChatMode.SCHEDULED

        if mode is None:
            raise SlackCommandError("commands/activate/invalid_mode.json")

        service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
        username = service.resolve_username(slack_user_id)
        first_name, last_name = service.resolve_name(slack_user_id)

        integration = SlackIntegration.find_or_create(
            slack_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            metadata={"team_id": team_id},
        )
        user = integration.user

        Session.close_all_open(user)

        user.activate(mode)

        return JsonTemplateLoader.ephemeral_response(
            "commands/activate/success.json", mode=mode
        )
