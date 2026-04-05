# Context Belongs to the Notification Layer

## Decision
Context — the space in which a conversation takes place — is the responsibility of the notification layer. As context evolves into a first-class abstraction, it should be introduced and managed there, rather than at the user or session layer.

## Considered Alternatives
- **Context as a user-layer concern** — Attaching context to the user or their integration profile. Rejected because a user can have multiple contexts; context is not a fixed property of who someone is, but of where a conversation is happening.
- **Context as a session-layer concern** — The session owns and resolves its own context. Closer, but the session's job is to track a conversation lifecycle, not to know how or where messages are delivered. That responsibility already belongs to the notification layer.

## Rationale
The notification layer already owns the "how and where to reach a user" concern. Context is a natural extension of that — it refines *where*, and the notification service is best positioned to interpret and act on it. Keeping context out of the user and session layers preserves clean boundaries and avoids leaking delivery concerns upward into the domain.
