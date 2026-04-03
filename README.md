# daily-notetaker

## Description
One-paragraph purpose

## Quickstart

### Prerequisites

- pyenv
- Python 3.14.3+
- PostgreSQL 17 (via Homebrew)

### 1. Python environment

```bash
pyenv local 3.14.3
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://daily_notetaker_user:yourpassword@localhost:5432/daily_notetaker_db
```

Generate a secret key with:

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

### 4. Database setup

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Common commands

## Project layout

## Link to deeper docs
