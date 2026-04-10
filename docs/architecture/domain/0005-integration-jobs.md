# IntegrationJob and Per-Integration Schedule Storage

## Decision
Introduce an `IntegrationJob` model to persist every scheduled notification attempt against a `UserIntegration`. The schedule itself is stored as a computed JSON object on `UserIntegration.metadata`. On any terminal state (`sent`, `failed`), the next `IntegrationJob` is computed by `ScheduleHandler` and persisted immediately, keeping the chain alive independent of job outcomes.

## Considered Alternatives

### Static Beat schedule with in-memory frequency computation
Frequency stored as a loose user metadata property, computed at dispatch time. Rejected because computed-in-memory schedules are invisible to admin views, Flower, and the audit trail. If the computation logic changes, historical reasoning is lost.

### `ScheduleConfig` model
A dedicated table storing per-user frequency and `next_prompt_at`. Considered and deferred in the initial domain ADR. Rejected at this stage in favour of `IntegrationJob`, which provides the same forward visibility with the added benefit of a full dispatch history. `ScheduleConfig` remains a future candidate if schedule complexity outgrows `UserIntegration.metadata`.

### Schedule stored on `User`
Attaching schedule metadata to the `User` model rather than `UserIntegration`. Rejected because the schedule is delivery-channel-specific — a user's Slack schedule and a future SMS schedule are independent concerns. Scoping to `UserIntegration` keeps channels cleanly separated.

### Pure cron loop without persisted next job
Beat polls for users due a prompt on a fixed interval, computing due time on the fly. Rejected because it provides no forward visibility (no admin view of upcoming jobs) and the schedule does not survive a failed dispatch — if a job fails, the chain must be reconstructed from frequency alone.

## Rationale
`IntegrationJob` makes the schedule a first-class database concern. Every scheduled notification is a row, so admin views, Flower, and the dispatcher all share a single source of truth. The chained recomputation pattern — next job persisted on any terminal state — ensures the schedule survives failures without additional recovery logic.

Storing the schedule as a computed JSON object on `UserIntegration.metadata` is appropriate at this stage. The schedule is channel-specific, complex enough to resist simple column normalisation, and will be affected by future integrations (e.g. calendar). Computation logic lives in `ScheduleHandler`, which already owns dispatch orchestration. `UserIntegration` exposes storage and appropriate getters/setters; the handler owns the computation.

The future introduction of a calendar integration is anticipated. At that point, a formal separation between notification integrations (which carry schedule metadata) and other integration types is the natural migration path. This is deferred deliberately — the current design does not preclude it.
