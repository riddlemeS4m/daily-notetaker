from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from django.db import models, transaction
from django.utils import timezone

from apps.core.constants import ChatMode
from apps.users.models import User

if TYPE_CHECKING:
    from apps.core.models.message import Message


class Session(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        AWAITING_RESPONSE = "awaiting_response", "Awaiting Response"
        CLOSED = "closed", "Closed"

    OPEN_STATUSES = frozenset({Status.ACTIVE, Status.AWAITING_RESPONSE})

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    chat_mode = models.CharField(max_length=20, choices=ChatMode.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "chat_mode", "status"],
                name="ix_session_user_mode_status",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "chat_mode"],
                condition=models.Q(status__in=["active", "awaiting_response"]),
                name="uq_one_open_session_per_user_mode",
            ),
        ]

    @classmethod
    def open(cls, user: User, chat_mode: ChatMode | str) -> Session:
        ChatMode.validate(chat_mode)
        return cls.objects.create(
            user=user, chat_mode=chat_mode, status=cls.Status.ACTIVE,
        )

    @classmethod
    def get_open(
        cls, user: User, chat_mode: ChatMode | str,
    ) -> Session | None:
        return cls.objects.filter(
            user=user,
            chat_mode=chat_mode,
            status__in=cls.OPEN_STATUSES,
        ).first()

    @classmethod
    def find_or_create(
        cls, user: User, chat_mode: ChatMode | str,
    ) -> Session:
        ChatMode.validate(chat_mode)
        with transaction.atomic():
            session = (
                cls.objects
                .select_for_update()
                .filter(
                    user=user,
                    chat_mode=chat_mode,
                    status__in=cls.OPEN_STATUSES,
                )
                .first()
            )
            if session is not None:
                return session
            return cls.objects.create(
                user=user, chat_mode=chat_mode, status=cls.Status.ACTIVE,
            )

    @classmethod
    def close_all_open(
        cls,
        user: User | None = None,
        chat_mode: ChatMode | None = None,
        stale_before: datetime | None = None,
    ) -> int:
        qs = cls.objects.filter(status__in=cls.OPEN_STATUSES)
        if user:
            qs = qs.filter(user=user)
        if chat_mode:
            qs = qs.filter(chat_mode=chat_mode)
        if stale_before:
            qs = qs.filter(updated_at__lt=stale_before)
        return qs.update(status=cls.Status.CLOSED, updated_at=timezone.now())

    def close(self) -> None:
        self.status = self.Status.CLOSED
        self.save(update_fields=["status", "updated_at"])

    def mark_awaiting(self) -> None:
        self.status = self.Status.AWAITING_RESPONSE
        self.save(update_fields=["status", "updated_at"])

    def add_message(
        self,
        role: str,
        content: str,
        template_key: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        return self.messages.create(
            role=role,
            content=content,
            template_key=template_key,
            metadata=metadata or {},
        )

    def __str__(self):
        return f"Session({self.user}, {self.chat_mode}, {self.status})"
