import logging

from celery import shared_task

from apps.core.models import Session

logger = logging.getLogger(__name__)


@shared_task
def close_end_of_day_sessions() -> None:
    """
    Fallback sweep that closes any sessions still open at end of day.
    Runs daily at 08:00 UTC via Celery Beat.
    """
    count = Session.close_all_open()
    if count:
        logger.info("End-of-day sweep closed %s session(s)", count)
