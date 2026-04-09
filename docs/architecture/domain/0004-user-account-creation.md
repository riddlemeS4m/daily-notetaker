# User Account Creation and Profile Data Source

## Decision
User accounts are created implicitly at Slack opt-in time. The Django `User` model
is populated with profile data (first name, last name, display name) sourced from
Slack's `users.info` API response at that moment. Opting in via Slack is treated as
the account creation event. A `claimed_at` timestamp on `User` tracks whether the
account has been explicitly formalized through a direct sign-in flow.

## Considered Alternatives

### Defer `User` creation until explicit sign-in (Option B)
Don't create a Django `User` row until the user signs in to the platform directly.
`UserIntegration` would exist without a `user_id` FK in the interim. Rejected
because it requires a schema change and adds complexity before there is any
direct sign-in UI or requirement for one.

### Create `User` with no profile data (status quo)
Use the Slack `external_id` as the username and leave name fields blank until
explicit sign-in. Rejected because it makes user-facing personalization
(e.g. "Hey Sam!") unavailable until a future sign-in flow is built, and leaks
a backend artifact into a user-facing field.

### Shadow account model with explicit status (Option A)
Create the `User` row at opt-in but model it as explicitly incomplete via an
`account_status` field (`shadow`, `claimed`). Rejected in favor of a simpler
`claimed_at` timestamp, which is consistent with the existing audit trail
pattern and carries the same semantic meaning with less ceremony.

## Rationale
An additional sign-up step before using the bot is not acceptable from a UX
standpoint and is unlikely to be a hard requirement for the foreseeable future.
Slack opt-in is the natural account creation boundary — the user has already
initiated the relationship. Populating profile fields from Slack at that point
is not presumptuous; it reflects data the user has already shared.

`claimed_at` provides a forward-compatible migration path: when a direct sign-in
UI is eventually built, the app can detect unclaimed accounts and prompt the user
to confirm or update their profile, then set `claimed_at` to formalize the record.
Profile data sourced from Slack can be overwritten at that point without any
structural changes to the schema.
