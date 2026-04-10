from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

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
class ScheduleSettingView(View):
    """
    Base view for /start and /end slash commands.
    Subclasses set the four class attributes to control which schedule
    bound they read and write.
    """

    setting_label: str
    default_setting: str
    getter_attr: str
    setter_attr: str

    def post(self, request, *args, **kwargs):
        integration = request.slack_integration
        text = request.slack_text

        if not text:
            current = getattr(integration, self.getter_attr)
            if current is None:
                current = getattr(settings, self.default_setting)
            return JsonTemplateLoader.ephemeral_response(
                "commands/schedules/current_value.json",
                setting=self.setting_label,
                value=current,
            )

        try:
            hour = int(text)
            getattr(integration, self.setter_attr)(hour)
        except (ValueError, TypeError) as ex:
            raise SlackCommandError(
                "commands/schedules/invalid_value.json",
                setting=self.setting_label,
            ) from ex

        return JsonTemplateLoader.ephemeral_response(
            "commands/schedules/success.json",
            setting=self.setting_label,
            value=hour,
        )
