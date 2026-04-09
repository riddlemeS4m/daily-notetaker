import functools
import logging

from django.conf import settings
from django.http import HttpResponse
from slack_sdk.signature import SignatureVerifier

from apps.core.services import JsonTemplateLoader
from apps.slack.models import SlackIntegration

logger = logging.getLogger(__name__)

_verifier = SignatureVerifier(signing_secret=settings.SLACK_SIGNING_SECRET)


def verify_slack_signature(view_func):
    """
    View decorator that rejects requests with an invalid or missing
    X-Slack-Signature header.  Uses slack_sdk's SignatureVerifier which
    checks HMAC-SHA256 and rejects timestamps older than 5 minutes
    (replay protection).
    """

    @functools.wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not _verifier.is_valid_request(request.body, dict(request.headers)):
            logger.warning(
                "Rejected request to %s — invalid Slack signature",
                request.path,
            )
            return HttpResponse(status=400)
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_slack_integration(view_func):
    """
    View decorator that resolves the SlackIntegration for the requesting
    Slack user (from POST ``user_id``) and sets ``request.slack_integration``.
    Returns an ephemeral error if no integration exists.
    """

    @functools.wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        slack_user_id = request.POST.get("user_id")
        try:
            request.slack_integration = SlackIntegration.for_external_id(
                slack_user_id
            )
        except SlackIntegration.DoesNotExist:
            return JsonTemplateLoader.ephemeral_response(
                "commands/mode/not_opted_in.json"
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
