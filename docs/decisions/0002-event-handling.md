# Notification Interface Abstraction

## Decision
Use an abstract `NotificationBackend` base class to decouple the core 
prompting logic from any specific notification service. Slack (and any 
future integrations) will implement this interface. Core services will 
only interact with the abstraction.

## Considered Alternatives
- **Django signals** — Core fires signals and Slack listens. Very loose 
  coupling, but harder to trace and reason about.
- **Celery task abstraction** — Prompts dispatched as tasks carrying a 
  `backend` parameter. Adds task infrastructure complexity without clear 
  benefit at this stage.

## Rationale
The Protocol/Interface class approach is explicit, testable, and 
well-documented — mirroring established Django patterns like the email 
backend system. It makes the contract between core and notification 
services clear and enforceable, and allows easy substitution of backends 
in both tests and future integrations.
