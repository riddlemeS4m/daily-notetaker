from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING, override
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.core.constants import ChatMode
from apps.core.handlers import SessionHandler
from apps.core.models import Message, Session
from apps.scheduled.models import IntegrationJob
from apps.users.models import User

if TYPE_CHECKING:
    from apps.users.models import UserIntegration

logger = logging.getLogger(__name__)


class ScheduleHandler(SessionHandler):
    """
    Handles scheduled prompt sessions.
    Owns schedule computation, job dispatch, and chained scheduling.
    """

    CHAT_MODE = ChatMode.SCHEDULED
    PROMPT_TEMPLATE_KEY = "scheduled/hourly_prompt.json"
    FIRST_PROMPT_TEMPLATE_KEY = "scheduled/first_prompt.json"
    LAST_PROMPT_TEMPLATE_KEY = "scheduled/last_prompt.json"

    PROMPT_INTERVAL_MINUTES = 120
    SCHEDULE_START_HOUR = 7
    SCHEDULE_END_HOUR = 19

    # ------------------------------------------------------------------
    # Inbound handling (user replies to a scheduled prompt)
    # ------------------------------------------------------------------

    @override
    def handle_inbound(self, user: User, content: str) -> None:
        session = Session.get_open(user, chat_mode=ChatMode.SCHEDULED)
        if session is None:
            return

        session.add_message(role=Message.Role.USER, content=content)

        if self.llm_service:
            result = self.generate_and_reply(user, session)
            if result.conversation_complete:
                session.close()
            else:
                session.mark_awaiting()

    # ------------------------------------------------------------------
    # Schedule computation
    # ------------------------------------------------------------------

    def compute_schedule(
        self, user: User, integration: UserIntegration,
    ) -> dict:
        """
        Build a one-day schedule and persist it on integration.metadata.
        Returns the schedule dict.
        """
        tz_name = self.notification_service.resolve_timezone(user)
        overrides = self.notification_service.resolve_schedule(user)

        start = overrides.get("schedule_start", self.SCHEDULE_START_HOUR)
        end = overrides.get("schedule_end", self.SCHEDULE_END_HOUR)
        freq = overrides.get("frequency_minutes", self.PROMPT_INTERVAL_MINUTES)

        start_min = start * 60
        end_min = end * 60

        slots = [start_min]
        cursor = start_min + freq
        while cursor < end_min:
            slots.append(cursor)
            cursor += freq
        # Always include end_hour as the final slot
        if slots[-1] != end_min:
            slots.append(end_min)

        schedule = {
            "frequency_minutes": freq,
            "start_hour": start,
            "end_hour": end,
            "timezone": tz_name,
            "slots": slots,
        }
        integration.metadata["schedule"] = schedule
        integration.save(update_fields=["metadata", "updated_at"])
        return schedule

    @staticmethod
    def _get_schedule(integration: UserIntegration) -> dict | None:
        return integration.metadata.get("schedule")

    def _ensure_schedule(
        self, user: User, integration: UserIntegration,
    ) -> dict:
        schedule = self._get_schedule(integration)
        if schedule is None:
            schedule = self.compute_schedule(user, integration)
        return schedule

    # ------------------------------------------------------------------
    # Slot → datetime helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _slot_to_time(slot_minutes: int) -> time:
        return time(hour=slot_minutes // 60, minute=slot_minutes % 60)

    @staticmethod
    def _slot_to_datetime(
        slot_minutes: int, date: datetime, tz: ZoneInfo,
    ) -> datetime:
        t = time(hour=slot_minutes // 60, minute=slot_minutes % 60)
        naive = datetime.combine(date, t)
        return naive.replace(tzinfo=tz)

    # ------------------------------------------------------------------
    # Template selection based on slot position
    # ------------------------------------------------------------------

    @classmethod
    def _template_for_slot(cls, slot_minutes: int, slots: list[int]) -> str:
        if slot_minutes == slots[0]:
            return cls.FIRST_PROMPT_TEMPLATE_KEY
        if slot_minutes == slots[-1]:
            return cls.LAST_PROMPT_TEMPLATE_KEY
        return cls.PROMPT_TEMPLATE_KEY

    # ------------------------------------------------------------------
    # Guard checks
    # ------------------------------------------------------------------

    def is_within_schedule(self, user: User) -> bool:
        tz_name = self.notification_service.resolve_timezone(user)
        overrides = self.notification_service.resolve_schedule(user)
        start = overrides.get("schedule_start", self.SCHEDULE_START_HOUR)
        end = overrides.get("schedule_end", self.SCHEDULE_END_HOUR)
        user_hour = datetime.now(ZoneInfo(tz_name)).hour

        if start <= end:
            return start <= user_hour <= end

        return user_hour >= start or user_hour <= end

    def is_dnd_blocked(self, user: User) -> bool:
        if not user.respect_dnd:
            return False
        return self.notification_service.is_dnd_active(user)

    # ------------------------------------------------------------------
    # Job dispatch (called by the beat task for each due IntegrationJob)
    # ------------------------------------------------------------------

    def dispatch_job(self, job: IntegrationJob) -> None:
        user = job.integration.user

        Session.close_all_open(user, chat_mode=ChatMode.SCHEDULED)

        if self.is_dnd_blocked(user):
            job.mark_skipped(reason="dnd")
            self.chain_next_job(job)
            return

        if not self.is_within_schedule(user):
            job.mark_skipped(reason="outside_schedule")
            self.chain_next_job(job)
            return

        try:
            schedule = self._ensure_schedule(user, job.integration)
            slot_min = self._scheduled_at_to_slot(job)
            template_key = self._template_for_slot(slot_min, schedule["slots"])

            session = Session.open(user, chat_mode=ChatMode.SCHEDULED)
            self.dispatch(user, session, template_key)

            first_message = session.messages.filter(
                role=Message.Role.BOT,
            ).first()
            job.mark_sent(message=first_message)
        except Exception as exc:
            logger.error("Failed to dispatch job %s: %s", job.id, exc)
            job.mark_failed(reason=str(exc))

        self.chain_next_job(job)

    @staticmethod
    def _scheduled_at_to_slot(job: IntegrationJob) -> int:
        """Convert a job's scheduled_at to a minutes-from-midnight slot."""
        schedule = job.integration.metadata.get("schedule", {})
        tz = ZoneInfo(schedule.get("timezone", "UTC"))
        local = job.scheduled_at.astimezone(tz)
        return local.hour * 60 + local.minute

    # ------------------------------------------------------------------
    # Chained scheduling
    # ------------------------------------------------------------------

    def chain_next_job(self, job: IntegrationJob) -> IntegrationJob | None:
        """
        Compute and persist the next IntegrationJob after a terminal job.
        Returns the new job, or None if the user is no longer eligible.
        """
        integration = job.integration
        user = integration.user

        if not user.is_opted_in or user.chat_mode != ChatMode.SCHEDULED:
            return None

        schedule = self._ensure_schedule(user, integration)
        tz = ZoneInfo(schedule["timezone"])
        now_local = timezone.now().astimezone(tz)
        slots = schedule["slots"]

        next_dt = self._find_next_slot(slots, now_local, tz)

        return IntegrationJob.objects.create(
            integration=integration,
            status=IntegrationJob.Status.SCHEDULED,
            scheduled_at=next_dt,
        )

    @staticmethod
    def _find_next_slot(
        slots: list[int], now_local: datetime, tz: ZoneInfo,
    ) -> datetime:
        """
        Find the next slot strictly after now_local.
        If no slots remain today, returns the first slot of the next day.
        """
        now_minutes = now_local.hour * 60 + now_local.minute

        for slot in slots:
            if slot > now_minutes:
                return datetime.combine(
                    now_local.date(), time(slot // 60, slot % 60), tzinfo=tz,
                )

        tomorrow = now_local.date() + timedelta(days=1)
        first_slot = slots[0]
        return datetime.combine(
            tomorrow, time(first_slot // 60, first_slot % 60), tzinfo=tz,
        )

    # ------------------------------------------------------------------
    # Seed schedule (entry point for activation / mode switch)
    # ------------------------------------------------------------------

    def seed_schedule(self, user: User) -> IntegrationJob:
        """
        Compute the schedule and create the first IntegrationJob for a user
        entering scheduled mode. Skips any existing pending jobs.
        """
        integration = self.notification_service._get_integration(user)

        IntegrationJob.objects.filter(
            integration=integration,
            status=IntegrationJob.Status.SCHEDULED,
        ).update(status=IntegrationJob.Status.SKIPPED)

        schedule = self.compute_schedule(user, integration)
        tz = ZoneInfo(schedule["timezone"])
        now_local = timezone.now().astimezone(tz)
        next_dt = self._find_next_slot(schedule["slots"], now_local, tz)

        return IntegrationJob.objects.create(
            integration=integration,
            status=IntegrationJob.Status.SCHEDULED,
            scheduled_at=next_dt,
        )

    # ------------------------------------------------------------------
    # Bulk cancellation (for mode switch away from scheduled)
    # ------------------------------------------------------------------

    @staticmethod
    def cancel_pending_jobs(integration: UserIntegration) -> int:
        return IntegrationJob.objects.filter(
            integration=integration,
            status=IntegrationJob.Status.SCHEDULED,
        ).update(status=IntegrationJob.Status.SKIPPED)
