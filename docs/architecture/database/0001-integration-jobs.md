# Integration Jobs

---

## Changes from initial design

### `UserIntegration` — updated
The `metadata` field now explicitly carries a computed schedule object for
notification integrations. Add the following to the **Notes** section:

> `metadata` carries backend-specific data including the computed schedule
> object for notification integrations (e.g. `frequency_minutes`,
> `next_prompt_at`, `timezone`). Getters and setters for schedule properties
> are exposed on the model; computation logic lives in `ScheduleHandler`.
> Non-notification integrations (e.g. future calendar integration) will not
> carry schedule metadata. A formal model separation is deferred until a
> calendar integration is introduced.

---

### `IntegrationJob` — new table

Persists every scheduled notification attempt against a `UserIntegration`.
Provides full forward visibility (upcoming jobs) and a complete dispatch
history (sent, failed, skipped).

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `integration_id` | int FK → UserIntegration | |
| `message_id` | int FK → Message, nullable | populated on dispatch |
| `status` | string | `scheduled`, `sent`, `failed`, `skipped` |
| `scheduled_at` | datetime | when this job is due to fire |
| `dispatched_at` | datetime, nullable | when dispatch was attempted |
| `metadata` | jsonb | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Notes:**
- The Beat dispatcher queries `status=scheduled, scheduled_at__lte=now()`
  to find due jobs.
- On any terminal state (`sent`, `failed`, `skipped`), `ScheduleHandler`
  computes and persists the next `IntegrationJob` immediately, keeping the
  schedule chain alive independent of job outcomes.
- `message_id` is populated once a `Message` row exists for the dispatch.
  Null for jobs that have not yet fired or were skipped before a message
  was produced.
- `scheduled_at` on the next job is computed from `UserIntegration.metadata`
  (schedule object) by `ScheduleHandler`, not derived from the current job's
  `dispatched_at`. This ensures the schedule survives failures without drift.
