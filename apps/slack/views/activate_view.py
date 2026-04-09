from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.core.models import Session
from apps.core.services import JsonTemplateLoader
from apps.slack.decorators import verify_slack_signature
from apps.slack.models import SlackIntegration

@method_decorator([csrf_exempt, verify_slack_signature], name="dispatch")
class ActivateView(View):
    """
    Handles the /activate <mode> slash command.
    Creates a User + SlackIntegration if they don't exist, sets mode and opt-in.
    """

    def post(self, request, *args, **kwargs):
        slack_user_id = request.POST.get("user_id")
        team_id = request.POST.get("team_id")
        mode = ChatMode.parse(request.POST.get("text", ""))

        if mode is None:
            return JsonTemplateLoader.ephemeral_response(
                "commands/activate/invalid_mode.json"
            )

        integration = SlackIntegration.find_or_create(
            slack_user_id, metadata={"team_id": team_id}
        )
        user = integration.user

        # user may have an open session from a previous opt-in
        Session.close_all_open(user)

        user.activate(mode)

        return JsonTemplateLoader.ephemeral_response(
            "commands/activate/success.json", mode=mode
        )
