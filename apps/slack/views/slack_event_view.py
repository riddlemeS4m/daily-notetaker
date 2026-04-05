import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.slack.models import SlackIntegration
from apps.slack.services import SlackNotificationService
from apps.slack.tasks import handle_slack_message

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class SlackEventView(View):
    """
    Receives Slack Events API payloads.
    Handles URL verification, validates the event, enqueues processing
    via Celery, and returns 200 within Slack's 3-second retry window.
    """

    def post(self, request, *args, **kwargs):
        if request.headers.get("X-Slack-Retry-Num"):
            return HttpResponse(status=200)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        if payload.get("type") == "url_verification":
            return JsonResponse({"challenge": payload["challenge"]})

        event = payload.get("event", {})
        if event.get("type") != "message" or event.get("bot_id"):
            return HttpResponse(status=200)

        service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
        parsed = service.read_response(payload)
        slack_user_id = parsed["external_id"]
        content = parsed["content"]

        user = SlackIntegration.get_user(slack_user_id)
        if user is None or not user.is_opted_in or not user.chat_mode:
            return HttpResponse(status=200)

        handle_slack_message.delay(user.chat_mode, slack_user_id, content)

        return HttpResponse(status=200)
