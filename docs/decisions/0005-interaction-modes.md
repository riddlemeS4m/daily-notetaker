# Interaction Mode Architecture

## Decision
Implement two separate Django apps — `scheduled` and `conversational` — 
each owning their own models, handlers, and logic. A top-level dispatcher 
routes incoming events to the correct app based on the user's active mode. 
The `conversational` app will include a `Session` model for tracking 
multi-turn interaction state.

## Considered Alternatives
- **Mode flag with conditional routing (Option A)** — A single `mode` field 
  on `UserProfile` with branching logic throughout the codebase. Simpler 
  upfront but mode becomes a cross-cutting concern that bleeds into every 
  layer.
- **Strategy pattern as primary architecture (Option C)** — A `Session` 
  model with a `handler` class reference as the top-level architectural 
  pattern. Appropriate data modeling for conversational state, but 
  unnecessarily complex as an organizing principle at this stage.

## Rationale
Separate apps enforce the boundary between modes structurally rather than 
relying on discipline. Each app can assume its own mode, eliminating 
cross-cutting conditional logic. The `Session` model is a data modeling 
concern scoped to the `conversational` app, not an architecture-level 
decision — the two concepts are complementary rather than competing.
