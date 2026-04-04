import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.handlers import SessionHandler
from apps.slack.models import SlackIntegration
from apps.slack.services import SlackNotificationService

logger = logging.getLogger(__name__)


def _get_notification_service() -> SlackNotificationService:
    return SlackNotificationService(token=settings.SLACK_BOT_TOKEN)


@method_decorator(csrf_exempt, name="dispatch")
class SlackEventView(View):
    """
    Receives Slack Events API payloads.
    Handles URL verification and routes inbound messages to the
    appropriate handler based on the user's chat_mode.
    """

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        if payload.get("type") == "url_verification":
            return JsonResponse({"challenge": payload["challenge"]})

        event = payload.get("event", {})
        if event.get("type") != "message" or event.get("bot_id"):
            return HttpResponse(status=200)

        service = _get_notification_service()
        parsed = service.read_response(payload)
        slack_user_id = parsed["external_id"]
        content = parsed["content"]

        user = SlackIntegration.get_user(slack_user_id)
        if user is None or not user.is_opted_in or not user.chat_mode:
            return HttpResponse(status=200)

        handler = SessionHandler.for_mode(
            user.chat_mode, notification_service=service
        )
        handler.handle_inbound(user=user, content=content)

        return HttpResponse(status=200)
