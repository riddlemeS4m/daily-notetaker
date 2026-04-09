from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.services import JsonTemplateLoader
from apps.slack.decorators import require_slack_integration, verify_slack_signature


@method_decorator(
    [csrf_exempt, verify_slack_signature, require_slack_integration],
    name="dispatch",
)
class DndView(View):
    """
    Handles the /dnd [on|off] slash command.
    Toggles or explicitly sets whether the app respects vendor DND
    when dispatching scheduled prompts to this user.
    """

    VALID_VALUES = {"on", "off"}

    def post(self, request, *args, **kwargs):
        user = request.slack_integration.user

        if not user.is_opted_in:
            return JsonTemplateLoader.ephemeral_response(
                "commands/dnd/not_opted_in.json"
            )

        text = request.POST.get("text", "").strip().lower()

        if text and text not in self.VALID_VALUES:
            return JsonTemplateLoader.ephemeral_response(
                "commands/dnd/invalid_value.json"
            )

        if text:
            new_value = text
        else:
            current = "on" if user.respect_dnd else "off"
            new_value = "off" if current == "on" else "on"

        user.set_dnd(new_value)

        return JsonTemplateLoader.ephemeral_response(
            "commands/dnd/success.json", value=new_value
        )
