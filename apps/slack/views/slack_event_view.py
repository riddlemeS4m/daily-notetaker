import json

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.exceptions import BadRequestError
from apps.slack.decorators import verify_slack_signature
from apps.slack.models import SlackIntegration
from apps.slack.services import SlackNotificationService
from apps.slack.tasks import handle_slack_message


@method_decorator([csrf_exempt, verify_slack_signature], name="dispatch")
class SlackEventView(View):
    """
    Receives Slack Events API payloads.
    Handles URL verification, validates the event, enqueues processing
    via Celery, and returns 200 within Slack's 3-second retry window.
    """

    def post(self, request, *args, **kwargs):
        # Ignore Slack retries to avoid duplicate processing
        if request.headers.get("X-Slack-Retry-Num"):
            return HttpResponse(status=200)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError as ex:
            raise BadRequestError("Invalid JSON in Slack event payload") from ex

        # Respond to Slack's one-time URL verification handshake
        if payload.get("type") == "url_verification":
            return JsonResponse({"challenge": payload["challenge"]})

        # Drop non-message events and bot-generated messages
        event = payload.get("event", {})
        if event.get("type") != "message" or event.get("bot_id"):
            return HttpResponse(status=200)

        service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
        parsed = service.read_response(payload)
        slack_user_id = parsed["external_id"]
        content = parsed["content"]

        # Skip users who haven't opted in or don't have an active chat mode
        user = SlackIntegration.get_user(slack_user_id)
        if user is None or not user.is_opted_in or not user.chat_mode:
            return HttpResponse(status=200)

        # Enqueue the message for async processing and ack immediately
        handle_slack_message.delay(user.chat_mode, slack_user_id, content)

        return HttpResponse(status=200)
