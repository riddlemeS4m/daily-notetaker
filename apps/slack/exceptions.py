from django.http import HttpResponse

from apps.core.exceptions import ApplicationError
from apps.core.services import JsonTemplateLoader


class SlackCommandError(ApplicationError):
    """
    Raised from Slack command views when user input is invalid.
    Renders an ephemeral Block Kit response via the error middleware.
    """

    status_code = 200

    def __init__(self, template_key: str, **kwargs: object) -> None:
        self.template_key = template_key
        self.kwargs = kwargs
        super().__init__(template_key)

    def to_response(self) -> HttpResponse:
        return JsonTemplateLoader.ephemeral_response(
            self.template_key, **self.kwargs
        )
