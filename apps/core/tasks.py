import logging

from celery import shared_task

from apps.core.models import Session

logger = logging.getLogger(__name__)


@shared_task
def close_end_of_day_sessions():
    """
    Fallback sweep that closes any sessions still open at end of day.
    Runs daily at 08:00 UTC via Celery Beat.
    """
    count = Session.objects.filter(
        status__in=[Session.Status.ACTIVE, Session.Status.AWAITING_RESPONSE],
    ).update(status=Session.Status.CLOSED)
    if count:
        logger.info("End-of-day sweep closed %s session(s)", count)
