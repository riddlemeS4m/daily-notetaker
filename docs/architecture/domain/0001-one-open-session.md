# Session Per Context

## Decision
A user should only ever be carrying on one conversation per context at a given point in time. A "context" is the space in which a conversation takes place — today that is always a direct message, but could eventually include channels, group threads, or other surfaces. The system should be designed with the understanding that a user may one day have multiple simultaneous open sessions, each belonging to a distinct context.

## Considered Alternatives
- **One active session per user, globally** — Simpler to reason about today, but assumes the bot will only ever operate in one space per user. This assumption is likely to break.
- **No formal position** — Leave session multiplicity as an implementation detail to sort out later. Risks coupling logic to an implicit one-session assumption that becomes expensive to unwind.

## Rationale
In the short to medium term, the bot only supports direct messages, so there will be at most one active session per user in practice. However, encoding a one-per-user assumption into the system makes future extension — channels, group messages, multi-surface support — a refactor rather than an addition. Introducing the concept of context now, even loosely, keeps that path open without requiring any immediate implementation work.
