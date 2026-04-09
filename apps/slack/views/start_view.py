from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.services import JsonTemplateLoader
from apps.slack.decorators import require_slack_integration, verify_slack_signature


@method_decorator(
    [csrf_exempt, verify_slack_signature, require_slack_integration],
    name="dispatch",
)
class StartView(View):
    """
    Handles the /start [hour] slash command.
    Sets or displays the user's schedule window start hour override.
    """

    def post(self, request, *args, **kwargs):
        user = request.slack_integration.user

        if not user.is_opted_in:
            return JsonTemplateLoader.ephemeral_response(
                "commands/schedules/not_opted_in.json"
            )

        text = request.POST.get("text", "").strip()
        integration = request.slack_integration

        if not text:
            current = integration.schedule_start or settings.SCHEDULE_START_HOUR
            return JsonTemplateLoader.ephemeral_response(
                "commands/schedules/current_value.json",
                setting="Schedule start hour",
                value=current,
            )

        try:
            hour = int(text)
        except ValueError:
            return JsonTemplateLoader.ephemeral_response(
                "commands/schedules/invalid_value.json",
                setting="Schedule start hour",
            )

        if not (0 <= hour <= 23):
            return JsonTemplateLoader.ephemeral_response(
                "commands/schedules/invalid_value.json",
                setting="Schedule start hour",
            )

        integration.set_schedule_start(hour)

        return JsonTemplateLoader.ephemeral_response(
            "commands/schedules/success.json",
            setting="Schedule start hour",
            value=hour,
        )
