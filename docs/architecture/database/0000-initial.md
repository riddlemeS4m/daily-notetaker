# Initial Database Architecture

---

## Overview
Four tables.
- `User` is the central entity.
- `UserIntegration` extends it with backend-specific identity. 
- `Session` tracks a single interaction lifecycle regardless of mode.
- `Message` stores every turn within a session, whether bot-generated or user-submitted.

---

## Tables

### `User`
Extends Django's built-in auth user. App-level fields are added directly
via a custom user model, avoiding a separate profile join for core queries.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `username` | string | inherited from auth |
| `email` | string | inherited from auth |
| `chat_mode` | string | `scheduled` or `conversational` |
| `opted_in_at` | datetime | |
| `opted_out_at` | datetime | |
| `metadata` | jsonb | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Notes:**
- `mode` reflects the user's currently active interaction mode, set via
  `/activate <mode>` and cleared on `/deactivate`.
- `opted_in_at` is the app-level opt-in flag. Django's own `is_active`
  controls account access and is not used for opt-in logic.

---

### `UserIntegration`
Holds backend-specific identity for a user. One row per backend per user.
Designed to accommodate multiple backends (e.g. Slack, SMS) without schema
changes.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `user_id` | int FK → User | |
| `vendor` | string | e.g. `slack`, `sms` |
| `external_id` | string | e.g. Slack user ID |
| `metadata` | JSON | backend-specific extras (e.g. `team_id`) |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Notes:**
- `external_id` is the identifier used by the backend to address the user
  (e.g. `slack_user_id`).
- `metadata` is a JSONField for anything backend-specific that doesn't
  warrant a dedicated column. For Slack, this includes `team_id`.
- A unique constraint on `(vendor, external_id)` prevents duplicate
  integrations.

---

### `Session`
Represents a single interaction lifecycle. Shared across both the scheduled
and conversational apps. The `source` field distinguishes how the session
was initiated without splitting the table.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `user_id` | int FK → User | |
| `chat_mode` | string | `scheduled` or `conversational` |
| `status` | string | e.g. `active`, `awaiting_response`, `closed` |
| `metadata` | jsonb | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Notes:**
- A scheduled session is opened by Celery beat and closed when the user
  responds or the response window expires.
- A conversational session is opened on first user message and closed
  when the exchange ends (definition TBD).
- `status` is currently a simple string. May evolve to a JSONField if
  multi-turn conversational state requires richer storage.

---

### `Message`
Stores every turn within a session — both bot-generated prompts and user
responses. `role` distinguishes direction; `template_key` records which
flat-file template was used for bot messages.

| Field | Type | Notes |
|---|---|---|
| `id` | int PK | |
| `session_id` | int FK → Session | |
| `role` | string | `bot` or `user` |
| `content` | text | the message body |
| `template_key` | string | nullable; e.g. `scheduled/hourly_prompt.json` |
| `metadata` | jsonb | |
| `created_at` | datetime | |
| `updated_at` | datetime | |

**Notes:**
- `template_key` is populated only for bot-generated messages that were
  rendered from a flat-file template. Null for user replies and LLM
  responses.
- Prompt/response pairs are modelled as two `Message` rows within the same `Session`.

---

## Considered alternatives

### Separate `PromptRecord` and `Message` tables
An earlier design kept a `PromptRecord` table in the scheduled app and a
`Message` table in the conversational app. Rejected because the data shape
is identical and splitting it would require the two apps to read from
different tables for what is fundamentally the same concept.

### Separate `UserProfile` and `SlackProfile` tables
An earlier design had a `UserProfile` table (holding `mode`, `is_active`)
sitting between `auth_user` and `SlackProfile`. Rejected because it added
a join with no conceptual benefit — `UserProfile` and `auth_user` represent
the same entity. App-level fields are now added directly to the custom
`User` model.

### `UserIntegration` as separate tables per backend
e.g. a `SlackProfile` table and a future `SMSProfile` table. Rejected
because it requires a schema change to add each new backend. A single
`UserIntegration` table with a `backend` discriminator field handles
multiple backends without migration.
