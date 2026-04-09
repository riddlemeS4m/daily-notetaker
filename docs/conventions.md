# Code Conventions

Patterns and style conventions observed and enforced across the codebase.
Not a Python style guide — focuses on architectural consistency, DRYness,
and where logic belongs.

---

## Models own their lifecycle

Business logic that mutates a model lives on the model, not in handlers,
views, or services. This keeps mutation logic in one place and makes it
testable without wiring up the full handler stack.

**Session examples:** `Session.find_or_create()`, `Session.close()`,
`Session.close_all_open()`, `Session.add_message()`, `Session.mark_awaiting()`

**User examples:** `User.activate(mode)`, `User.deactivate()`,
`User.switch_mode(mode)`

When a model method needs to return useful context to the caller (e.g.
`switch_mode` returns the previous mode), prefer that over requiring the
caller to read state before mutating.

---

## Abstract base classes define contracts

The two abstraction axes — `NotificationService` (how you communicate) and
`SessionHandler` (how you orchestrate) — are defined as ABCs. Concrete
implementations override abstract methods; shared behavior lives on the
base class only when it genuinely applies to all implementations.

`LLMService` follows the same pattern for the LLM vendor axis.

### Auto-registration via `__init_subclass__`

`SessionHandler` subclasses declare a `CHAT_MODE` class attribute and are
automatically registered. Resolution is via `SessionHandler.for_mode()`.
No manual registry or import-time side effects required — just defining
the class is enough.

### `@override` on all overridden methods

Use `typing.override` on every method that overrides an abstract (or
concrete) base class method. This makes the contract relationship explicit
and catches renames at type-check time.

---

## Shared logic on the base handler

When two or more handlers share an identical multi-step pattern, extract
it to a method on `SessionHandler` rather than duplicating it.

**`dispatch()`** — sends a prompt, records the bot message, marks the
session as awaiting response.

**`generate_and_reply()`** — calls the LLM, persists the bot reply,
sends it to the user. Returns the `GenerateResult` so callers can
inspect it (e.g. to check `conversation_complete`).

Handlers should read as a short sequence of high-level steps, not
low-level ORM calls.

---

## Guard clauses at the boundary, not deep in the stack

Eligibility checks (opted in? correct mode? valid user?) happen at the
**entry point** — the view or Celery task — not inside the handler.
Handlers assume they are called with a valid, eligible user. This avoids
duplicating guards across every layer and makes handlers easier to test.

---

## Decorators over middleware for scoped concerns

Use **view decorators** for concerns that apply to a specific set of
views rather than every request. Middleware is reserved for truly global
concerns.

- `verify_slack_signature` — applied to all Slack views via
  `@method_decorator`
- `require_slack_integration` — applied to views that need a resolved
  `SlackIntegration` on the request
- `ErrorHandlingMiddleware` — global; catches `ApplicationError`
  subclasses and unhandled exceptions

Decorators compose via a list passed to `method_decorator`:
```python
@method_decorator([csrf_exempt, verify_slack_signature, require_slack_integration], name="dispatch")
```

---

## Centralised error handling

Application-level errors extend `ApplicationError`, which carries a
`status_code`. `ErrorHandlingMiddleware` catches these and returns the
appropriate HTTP response. This eliminates per-view `try/except` blocks
for expected errors.

Use the hierarchy — don't catch-log-reraise:

| Class | Code | Use |
|---|---|---|
| `ApplicationError` | 500 | Base; unexpected application error |
| `BadRequestError` | 400 | Malformed or missing request data |
| `ExternalServiceError` | 502 | Third-party API failure |

If an external SDK raises its own exception (e.g. `SlackApiError`,
`openai.APIError`), let it propagate — the middleware logs it and
returns 500. Only wrap in `ExternalServiceError` when you need to
add context or change the status code.

---

## Template responses

Slack Block Kit templates live as flat JSON files under `templates/slack/`.
`JsonTemplateLoader` handles loading, `$variable` substitution, and
plain-text extraction.

For the common pattern of returning an ephemeral Slack slash-command
response, use the one-liner:

```python
return JsonTemplateLoader.ephemeral_response("commands/activate/success.json", mode=mode)
```

This replaces the repeated load → build dict → `JsonResponse` pattern.

---

## Race condition patterns

When two concurrent requests can create the same resource:

- **Session:** `find_or_create` uses `select_for_update()` inside
  `transaction.atomic()` — row-level locking prevents duplicates.
- **SlackIntegration:** `find_or_create` uses try/create/except
  `IntegrityError` with a re-fetch — relies on the unique constraint
  to resolve the race. The create is wrapped in its own
  `transaction.atomic()` so the `IntegrityError` doesn't poison the
  outer transaction.

Pick the pattern that fits: `select_for_update` when the row already
exists most of the time; try/except `IntegrityError` when creates are
rare and the unique constraint is the source of truth.

---

## Logging

Log **operational signals**, not control flow. If the message would be
`logger.debug("Entering function X")` or `logger.info("Doing Y for
user %s")`, skip it. The code structure already communicates that.

Good uses of logging:
- Celery task outcomes: `"Expired %s stale scheduled session(s)"`
- Security events: `"Rejected request — invalid Slack signature"`
- Unrecoverable errors in the middleware

---

## Type annotations

- Use `X | None` union syntax (not `Optional[X]`).
- Use `from __future__ import annotations` when a file needs forward
  references (e.g. a model referencing itself or a not-yet-defined type).
  Not required in every file — only where needed.
- Annotate return types on public model methods and service methods.
- Use `dict[str, Any]` over bare `dict` for payload-style parameters.
