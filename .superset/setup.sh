#!/usr/bin/env bash
set -euo pipefail

WORKTREE_DIR="$(pwd)"
WORKTREE_NAME="$(basename "$WORKTREE_DIR")"
MAIN_WORKTREE="$(git worktree list --porcelain | head -1 | sed 's/worktree //')"

if [ "$WORKTREE_DIR" = "$MAIN_WORKTREE" ]; then
    echo "Error: This script is intended for git worktrees, not the main checkout."
    exit 1
fi

if [ ! -f "$MAIN_WORKTREE/.env" ]; then
    echo "Error: No .env found in main worktree ($MAIN_WORKTREE)"
    echo "Please create a .env file in the main worktree first."
    exit 1
fi

echo "==> Setting up worktree: $WORKTREE_NAME"

# --- Create and activate venv, install dependencies ---
echo "==> Setting up Python virtual environment"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements-dev.txt

# --- Copy .env from main worktree ---
echo "==> Copying .env from main worktree"
cp "$MAIN_WORKTREE/.env" "$WORKTREE_DIR/.env"

# --- Derive worktree-specific values ---
PORT=$(python3 -c "import hashlib; print(8001 + int(hashlib.md5('$WORKTREE_NAME'.encode()).hexdigest(), 16) % 999)")
FLOWER_PORT=$((PORT + 1000))

DB_SUFFIX=$(echo "$WORKTREE_NAME" | tr '-' '_' | tr '[:upper:]' '[:lower:]')
DB_NAME="daily_notetaker_db_${DB_SUFFIX}"

ORIGINAL_DB_URL=$(grep '^DATABASE_URL=' "$WORKTREE_DIR/.env" | cut -d= -f2-)
DB_BASE=$(echo "$ORIGINAL_DB_URL" | sed 's|/[^/]*$||')
NEW_DB_URL="${DB_BASE}/${DB_NAME}"

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# --- Override env vars (portable across macOS and Linux) ---
echo "==> Configuring .env"
python3 -c "
import sys

env_path = sys.argv[1]
updates = dict(pair.split('=', 1) for pair in sys.argv[2:])

with open(env_path, 'r') as f:
    lines = f.readlines()

result = []
seen = set()
for line in lines:
    stripped = line.strip()
    if '=' in stripped and not stripped.startswith('#'):
        key = stripped.split('=', 1)[0]
        if key in updates:
            result.append(f'{key}={updates[key]}\n')
            seen.add(key)
            continue
    result.append(line)

for key, value in updates.items():
    if key not in seen:
        result.append(f'{key}={value}\n')

with open(env_path, 'w') as f:
    f.writelines(result)
" "$WORKTREE_DIR/.env" \
    "DATABASE_URL=$NEW_DB_URL" \
    "SECRET_KEY=$SECRET_KEY" \
    "PORT=$PORT" \
    "FLOWER_PORT=$FLOWER_PORT"

echo "    PORT=$PORT"
echo "    FLOWER_PORT=$FLOWER_PORT"
echo "    DATABASE=$DB_NAME"

# --- Create PostgreSQL database (using local superuser for admin ops) ---
echo "==> Creating database: $DB_NAME"
DB_USER=$(python3 -c "from urllib.parse import urlparse; print(urlparse('${ORIGINAL_DB_URL}').username)")
DB_HOST=$(python3 -c "from urllib.parse import urlparse; print(urlparse('${ORIGINAL_DB_URL}').hostname)")
DB_PORT=$(python3 -c "from urllib.parse import urlparse; print(urlparse('${ORIGINAL_DB_URL}').port)")

CREATEDB_OUTPUT=$(createdb -h "$DB_HOST" -p "$DB_PORT" -U postgres -O "$DB_USER" "$DB_NAME" 2>&1) || {
    if echo "$CREATEDB_OUTPUT" | grep -q "already exists"; then
        echo "    Database $DB_NAME already exists, continuing..."
    else
        echo "Error creating database: $CREATEDB_OUTPUT"
        exit 1
    fi
}

# --- Run migrations ---
echo "==> Running migrations"
python manage.py migrate --no-input

# --- Create admin superuser ---
echo "==> Creating admin superuser"
DJANGO_SUPERUSER_PASSWORD=topsecretpassword python manage.py createsuperuser \
    --noinput \
    --username admin \
    --email admin@admin.com 2>/dev/null \
    || echo "    Admin user may already exist, continuing..."

echo "==> Setup complete!"
echo "    Run './.superset/run.sh' to start the app on port $PORT"
