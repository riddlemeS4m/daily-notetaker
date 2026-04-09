class ApplicationError(Exception):
    """Base for all application-level errors."""

    status_code = 500


class BadRequestError(ApplicationError):
    """The request payload is malformed or missing required data."""

    status_code = 400


class ExternalServiceError(ApplicationError):
    """A third-party API call failed."""

    status_code = 502
