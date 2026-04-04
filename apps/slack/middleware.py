import logging

from django.conf import settings
from django.http import HttpResponse
from slack_sdk.signature import SignatureVerifier

logger = logging.getLogger(__name__)


class SlackSignatureMiddleware:
    """
    Verifies the X-Slack-Signature header on all requests under /slack/.
    Rejects requests with invalid or missing signatures with a 400.
    Uses slack_sdk.signature.SignatureVerifier which checks HMAC-SHA256
    and rejects timestamps older than 5 minutes (replay protection).
    """

    SLACK_URL_PREFIX = "/slack/"

    def __init__(self, get_response):
        self.get_response = get_response
        self.verifier = SignatureVerifier(
            signing_secret=settings.SLACK_SIGNING_SECRET,
        )

    def __call__(self, request):
        if request.path.startswith(self.SLACK_URL_PREFIX):
            body = request.body
            headers = dict(request.headers)
            if not self.verifier.is_valid_request(body, headers):
                logger.warning(
                    "Rejected request to %s — invalid Slack signature",
                    request.path,
                )
                return HttpResponse(status=400)

        return self.get_response(request)
