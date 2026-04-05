# Conversation Completion Framework

## Decision
Use a structured, coverage-based completion framework. The LLM tracks explicit
coverage state across four Tier 1 categories (accomplishments, in_progress,
blockers, tomorrow_priorities) and returns a `categories_covered` array plus a
`conversation_complete` boolean in every JSON response. The conversation is marked
complete when all four categories are covered, or when the user explicitly signals
they are done.

Each category allows at most one follow-up question. The LLM probes uncovered
categories in priority order, at most one per turn, and skips any the user has
already addressed unprompted.

## Considered Alternatives

**Implicit coverage** — the LLM infers coverage from conversation context and
marks complete using its own judgment. Simpler prompt, but produces inconsistent
behavior and gives no auditable record of what was captured in a given session.

**Turn-count based completion** — the conversation ends after a fixed number of
exchanges. Predictable, but risks cutting off mid-thought or padding when the user
is done early.

**Signal-only completion** — the LLM detects natural closure cues from the user
("that's it", "nothing else") and marks complete reactively. Suitable as an escape
hatch but insufficient as a primary strategy since many users won't signal closure
explicitly.

## Rationale
Explicit coverage state makes the LLM's behavior deterministic and testable.
`categories_covered` gives an auditable, per-session record of what was captured,
which directly enables future features such as per-category completion analytics,
detecting categories a user consistently skips, and longitudinal insight generation.
A coverage-based approach also maps cleanly to the extensible category registry
design (Tier 1 / Tier 2 / Tier 3), where Tier 1 categories drive active probing
and Tier 2+ are derived or pulled later without changing the completion contract.
