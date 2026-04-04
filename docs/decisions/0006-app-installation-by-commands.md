# Slash Command Arguments

## Decision
The `/activate` slash command accepts mode as an argument 
(e.g. `/activate scheduled`, `/activate conversational`). A corresponding 
`/deactivate` command requires no argument — it deactivates the user 
regardless of mode.

## Considered Alternatives
- **Separate commands per mode** — `/activate-scheduled`, 
  `/activate-conversational`, etc. More Slack commands to register and 
  maintain, less extensible.
- **Interactive modal** — `/activate` triggers a Block Kit modal for 
  preference configuration. Better UX long-term but unnecessary overhead 
  at this stage.

## Rationale
Passing mode as an argument keeps the command surface small while remaining 
extensible — additional arguments or modes can be added without registering 
new Slack commands. It's also the most readable pattern for a technical 
user base and maps cleanly to the two-app architecture decided in Decision 5.
