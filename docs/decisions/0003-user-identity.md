# User Identity & Opt-In

## Decision
Create a headless Django `User` on `/activate`, linked to a 
backend-agnostic `UserProfile` model, which is in turn extended by a 
`SlackProfile` carrying Slack-specific identity (`slack_user_id`, 
`team_id`). The Django `User` has no password or login mechanism at this 
stage.

## Considered Alternatives
- **Slack user ID as primary identity** — No Django `User` at all. 
  Simpler now, but requires a painful migration if a frontend with 
  authentication is ever added.
- **Thin profile only, no Django User** — Keeps things lightweight and 
  backend-agnostic, but foregoes the Django `User` foundation that the 
  long-term frontend will almost certainly need.

## Rationale
A headless Django `User` adds minimal overhead now while future-proofing 
the frontend. Keeping Slack-specific identity isolated in `SlackProfile` 
preserves the decoupling goal — the core app never needs to know a user 
came from Slack. Other notification backends can introduce their own 
profile extensions without touching core models.
