from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.constants import ChatMode
from apps.core.services import JsonTemplateLoader
from apps.scheduled.handlers import ScheduleHandler
from apps.slack.decorators import (
    require_opted_in,
    require_slack_integration,
    verify_slack_signature,
)
from apps.slack.exceptions import SlackCommandError
from apps.slack.services import SlackNotificationService


@method_decorator(
    [csrf_exempt, verify_slack_signature, require_slack_integration, require_opted_in],
    name="dispatch",
)
class FrequencyView(View):
    """
    Handles the /frequency [minutes] slash command.
    Sets or displays how often the user is prompted (in minutes).
    """

    def post(self, request, *args, **kwargs):
        integration = request.slack_integration
        user = integration.user
        text = request.slack_text

        if not text:
            current = integration.frequency_minutes
            if current is None:
                current = ScheduleHandler.PROMPT_INTERVAL_MINUTES
            return JsonTemplateLoader.ephemeral_response(
                "commands/schedules/frequency_current.json",
                value=current,
            )

        try:
            integration.set_frequency_minutes(int(text))
        except (ValueError, TypeError) as ex:
            raise SlackCommandError(
                "commands/schedules/frequency_invalid.json",
            ) from ex

        if user.chat_mode == ChatMode.SCHEDULED and user.is_opted_in:
            service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
            handler = ScheduleHandler(notification_service=service)
            handler.compute_schedule(user, integration)
            handler.seed_schedule(user)

        return JsonTemplateLoader.ephemeral_response(
            "commands/schedules/frequency_success.json",
            value=integration.frequency_minutes,
        )
