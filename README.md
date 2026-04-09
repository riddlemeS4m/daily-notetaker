# daily-notetaker

A Slack-integrated daily note-taking bot that captures structured end-of-day notes from users via two interaction modes: **scheduled** (bot-initiated prompts on a timer) and **conversational** (user-initiated, multi-turn). Backed by OpenAI for natural conversation, Celery for async processing and scheduled tasks, and PostgreSQL for persistence.

## Quickstart

### Prerequisites

- pyenv with Python 3.14+
- PostgreSQL 17 (via Homebrew)
- Redis (for Celery broker/result backend)

### 1. Python environment

```bash
pyenv local 3.14
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

See `.env.example` for the full list. At minimum you need:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `CELERY_BROKER_URL` | Redis URL for Celery |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery results |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token |
| `SLACK_SIGNING_SECRET` | Slack request signing secret |
| `OPENAI_API_KEY` | OpenAI API key |

Generate a Django secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. PostgreSQL

```bash
brew services start postgresql@17
createdb daily_notetaker_db
psql postgres -c "CREATE USER daily_notetaker_user WITH PASSWORD 'yourpassword';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE daily_notetaker_db TO daily_notetaker_user;"
psql daily_notetaker_db -c "GRANT ALL ON SCHEMA public TO daily_notetaker_user;"
```

### 4. Run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In separate terminals, start the Celery worker and beat scheduler:

```bash
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

### Docker

The project ships with a `Dockerfile` and `docker-compose.yml` that run three services: **web** (gunicorn), **worker** (Celery), and **beat** (Celery Beat). PostgreSQL and Redis are expected externally.

```bash
docker compose up -d
```

## Common commands

```bash
python manage.py runserver                        # Dev server
python manage.py migrate                          # Apply migrations
python manage.py makemigrations                   # Generate migrations
python manage.py createsuperuser                  # Create admin user
celery -A config worker --loglevel=info           # Celery worker
celery -A config beat --loglevel=info             # Celery beat scheduler
```

## Project layout

```
config/                     Django project settings, URLs, WSGI, Celery
apps/
  core/                     Sessions, messages, LLM/notification ABCs, error handling
  users/                    Custom User model with opt-in/mode management
  slack/                    Slack Events API, slash command views, notification service
  openai/                   OpenAI LLM service implementation
  scheduled/                Scheduled-mode handler and Celery beat tasks
  conversational/           Conversational-mode handler
templates/
  llm/                      System prompt for OpenAI
  slack/                    Slack Block Kit JSON templates (commands, prompts)
docs/                       Architecture, decisions, conventions
```

## Docs

Detailed documentation lives in `docs/`:

- **[conventions](docs/conventions.md)** — code style and architectural patterns
- **[architecture/](docs/architecture/)** — domain model, database, and data-flow diagrams
- **[decisions/](docs/decisions/)** — architectural decision records (ADRs)
