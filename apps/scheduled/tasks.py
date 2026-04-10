import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.scheduled.models import IntegrationJob
from apps.slack.services import SlackNotificationService

logger = logging.getLogger(__name__)


@shared_task
def dispatch_due_jobs_task():
    """
    Poll for IntegrationJobs that are due and dispatch each one.
    Runs every minute via Celery Beat.
    """
    now = timezone.now()

    # --- Temporary early-exit optimisation (removable) ---
    # If the earliest pending job is more than 2 minutes away, skip this cycle.
    earliest = (
        IntegrationJob.objects.filter(
            status=IntegrationJob.Status.SCHEDULED,
        )
        .order_by("scheduled_at")
        .values_list("scheduled_at", flat=True)
        .first()
    )
    if earliest is None or earliest > now + timezone.timedelta(minutes=2):
        return
    # --- End early-exit optimisation ---

    from apps.scheduled.handlers import ScheduleHandler

    service = SlackNotificationService(token=settings.SLACK_BOT_TOKEN)
    handler = ScheduleHandler(notification_service=service)

    due_jobs = (
        IntegrationJob.objects.filter(
            status=IntegrationJob.Status.SCHEDULED,
            scheduled_at__lte=now,
        )
        .select_related("integration__user")
    )

    for job in due_jobs:
        try:
            handler.dispatch_job(job)
        except Exception:
            logger.exception("Unhandled error dispatching job %s", job.id)
