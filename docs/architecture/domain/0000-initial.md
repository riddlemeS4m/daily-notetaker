# Initial Domain Architecture

---

## Design principles

**Two abstraction axes.** The domain has two clean orthogonal abstractions:
*how you communicate* (`NotificationService`) and *how you orchestrate*
(`SessionHandler`). Everything else is concrete. New vendors extend the
notification axis; new interaction modes extend the handler axis.

**Contract over implementation.** Abstract base classes define what a
service or handler *must* do. Concrete implementations override where their
context demands it. Shared default behavior lives on the base class where
it genuinely applies to all implementations.

**Apps own behavior, not data.** `Session` and `Message` are shared models
that live above both apps. The `scheduled` and `conversational` apps own
handlers and flow logic, not their own tables. Both apps read and write the
same data layer.

**Defer complexity.** DND awareness is handled at runtime via the Slack API
(using the appropriate bot scope) rather than stored state. Prompt frequency
is a hardcoded constant for now. `LLMService` is stubbed inside the
conversational app and not wired to anything until needed.

---

## Components

### `NotificationService`
Abstract base class defining the contract for all notification vendors.
Any vendor integration must implement this interface.

| Method | Description |
|---|---|
| `send_prompt(user, template)` | Sends a bot-initiated message to a user |
| `read_response(payload)` | Parses an inbound response payload into a `Message` |

**Notes:**
- Implementations may override either method where vendor behavior differs.
- The service is vendor-agnostic at the call site — callers never reference
  `SlackNotificationService` directly.

---

### `SlackNotificationService`
Concrete implementation of `NotificationService` for Slack.

**Notes:**
- Reads `UserIntegration` to resolve `external_id` (Slack user ID) and
  `metadata` (e.g. `team_id`) for API calls.
- Checks DND status via the Slack API at send time using the bot's DND
  scope. DND state is not stored.
- Renders messages from flat-file Block Kit templates via `MessageTemplate`.

---

### `MessageTemplate`
Utility that loads Slack Block Kit JSON from flat files at runtime.

**Notes:**
- Templates live in `templates/slack/`. The `template_key` field on
  `Message` (e.g. `scheduled/hourly_prompt.json`) is the relative path
  used to load the file.
- No database involvement. Template changes are deployed as file changes.

---

### `SessionHandler`
Abstract base class defining the contract for session lifecycle and message
orchestration. Both concrete handlers implement this interface.

| Method | Description |
|---|---|
| `open_session(user)` | Creates and persists a new `Session` |
| `close_session(session)` | Marks a `Session` as closed |
| `write_message(session, role, content, template_key)` | Persists a `Message` to a `Session` |
| `dispatch(user, session, template_key)` | Sends a prompt via `NotificationService` |
| `handle(...)` | Entry point — implemented differently by each subclass |

**Notes:**
- `open_session`, `close_session`, `write_message`, and `dispatch` have
  default implementations on the base class and may be overridden.
- `handle()` has no default — each subclass defines its own flow.

---

### `ScheduleHandler`
Concrete implementation of `SessionHandler` for the scheduled app.
Push-initiated: Celery beat triggers `handle()` on a fixed interval.

**Flow:**
1. Check user DND status via `SlackNotificationService`
2. If DND is inactive, call `open_session()`
3. Call `dispatch()` to send the hourly prompt
4. Await inbound response (routed back via the Slack webhook)
5. Call `write_message()` for the response, then `close_session()`

**Notes:**
- Prompt frequency is a hardcoded constant (1 hour). No `ScheduleConfig`
  model is needed at this stage.
- Sessions opened by `ScheduleHandler` have `chat_mode = "scheduled"`.

---

### `ConversationHandler`
Concrete implementation of `SessionHandler` for the conversational app.
Pull-initiated: an inbound Slack message triggers `handle()`.

**Flow:**
1. Look up or open a `Session` for the user
2. Call `write_message()` for the inbound user message
3. Generate a reply (via `LLMService` when wired; stubbed for now)
4. Call `dispatch()` to send the reply
5. Keep session open for follow-up turns; close on inactivity or explicit end

**Notes:**
- Sessions managed by `ConversationHandler` have `chat_mode = "conversational"`.
- `LLMService` is a stub inside the conversational app. It is not wired to
  any external API at this stage.

---

### `LLMService`
Stub service inside the conversational app. Intended to wrap future LLM
API calls for generating conversational replies.

**Notes:**
- Not implemented in the initial build. `ConversationHandler` returns a
  hardcoded or template-based reply until this is wired up.

---

## App structure

### `scheduled` app
Owns `ScheduleHandler` and the Celery beat task that triggers it.
Reads and writes shared `Session` and `Message` models.

### `conversational` app
Owns `ConversationHandler` and `LLMService`.
Reads and writes shared `Session` and `Message` models.

---

## Considered alternatives

### Separate `PromptRecord` model in the scheduled app
An earlier design had the scheduled app tracking sent prompts in its own
table. Rejected in favour of shared `Session` and `Message` models — the
data shape is identical across modes and splitting it creates unnecessary
divergence.

### No `SessionHandler` abstraction
Keeping `ScheduleHandler` and `ConversationHandler` fully independent with
shared logic extracted into utility functions. Rejected because the session
lifecycle contract (`open`, `close`, `write_message`, `dispatch`) is
substantial enough to warrant a formal interface, and the symmetry with
`NotificationService` reinforces a consistent architectural pattern.

### `ScheduleConfig` model for frequency and DND
Storing frequency and DND preferences in the database. Rejected at this
stage — frequency is a constant and DND is read from the Slack API at
runtime. A `ScheduleConfig` model can be introduced later if per-user
scheduling preferences are needed.

### Tightly coupled Slack handler logic
Embedding Slack-specific dispatch and response parsing directly in the
handlers. Rejected because it would couple orchestration logic to a
specific vendor, violating the `NotificationService` abstraction.
