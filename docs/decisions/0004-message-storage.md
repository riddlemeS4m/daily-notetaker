# Message Template Storage

## Decision
Store Slack Block Kit JSON templates as flat files in a `templates/slack/` 
directory, loaded at runtime. Templates are versioned and deployed alongside 
code.

## Considered Alternatives
- **Database model** — `MessageTemplate` model with a `body` JSONField, 
  editable via Django admin. More flexible at runtime but loses versioning 
  discipline.
- **Hybrid (files + DB overrides)** — Files as defaults, DB overrides per 
  Django's template loader chain. More powerful but adds complexity without 
  clear need.

## Rationale
Message templates are more like configuration than data — they change 
infrequently, and when they do change, that change should be deliberate, 
reviewed, and versioned. Flat files enforce that discipline naturally. 
Storing them in a `templates/slack/` directory also means minimal code 
changes are needed to update a template, similar to updating a docs or 
config directory. This also keeps the DB schema simpler at this stage.
