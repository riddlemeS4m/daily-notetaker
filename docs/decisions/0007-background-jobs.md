# Task Queue & Scheduler Selection

## Decision
Use **Celery** (with Celery Beat) as the task queue and periodic task scheduler, backed by Redis as the message broker.

## Considered Alternatives

- **APScheduler** — A lightweight in-process Python scheduler. Simple to set up, but runs inside the Django process, making it fragile under restarts and difficult to scale horizontally. No native support for distributed task execution.
- **Django-Q** — A Django-native task queue with scheduling support. Tighter Django integration than Celery, but a smaller community, less mature tooling, and fewer integrations compared to the Celery ecosystem.
- **Cron / system scheduler** — Simple and dependency-free, but tightly coupled to the host OS. Offers no visibility into task state, no retry logic, and no path to distributed execution. Would require additional tooling to achieve feature parity with Celery Beat.

## Rationale

The app's core feature — periodically prompting opted-in users based on their schedules — requires a reliable, inspectable periodic task system. Celery Beat provides exactly this: a first-class scheduler that runs as a managed process alongside the Django app, with database-backed schedules that can be adjusted at runtime without redeploying.

Beyond scheduling, Celery decouples task execution from the web/bot process, meaning Slack webhook handlers can enqueue work and return immediately rather than blocking. This also opens a clean path to scaling workers independently as the user base grows.

Redis was already a natural fit as a broker given its speed and widespread use in Django deployments, and the Celery + Redis + Django combination has broad community support, mature documentation, and well-understood operational patterns.
