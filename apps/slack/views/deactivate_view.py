from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.models import Session
from apps.core.services import JsonTemplateLoader
from apps.scheduled.handlers import ScheduleHandler
from apps.slack.decorators import (
    require_opted_in,
    require_slack_integration,
    verify_slack_signature,
)


@method_decorator(
    [csrf_exempt, verify_slack_signature, require_slack_integration, require_opted_in],
    name="dispatch",
)
class DeactivateView(View):
    """
    Handles the /deactivate slash command.
    Sets opted_out_at on the User, stopping further prompts.
    """

    def post(self, request, *args, **kwargs):
        integration = request.slack_integration
        user = integration.user

        user.deactivate()
        Session.close_all_open(user)
        ScheduleHandler.cancel_pending_jobs(integration)

        return JsonTemplateLoader.ephemeral_response(
            "commands/deactivate/success.json"
        )
