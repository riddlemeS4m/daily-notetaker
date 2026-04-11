#!/usr/bin/env bash
set -euo pipefail

WORKTREE_DIR="$(pwd)"
WORKTREE_NAME="$(basename "$WORKTREE_DIR")"

echo "==> Tearing down worktree: $WORKTREE_NAME"

# --- Derive database name ---
DB_SUFFIX=$(echo "$WORKTREE_NAME" | tr '-' '_' | tr '[:upper:]' '[:lower:]')
DB_NAME="daily_notetaker_db_${DB_SUFFIX}"

# --- Parse connection info from .env ---
if [ -f "$WORKTREE_DIR/.env" ]; then
    DB_URL=$(grep '^DATABASE_URL=' "$WORKTREE_DIR/.env" | cut -d= -f2-)
else
    MAIN_WORKTREE="$(git worktree list --porcelain | head -1 | sed 's/worktree //')"
    DB_URL=$(grep '^DATABASE_URL=' "$MAIN_WORKTREE/.env" | cut -d= -f2-)
fi

DB_HOST=$(python3 -c "from urllib.parse import urlparse; print(urlparse('${DB_URL}').hostname)")
DB_PORT=$(python3 -c "from urllib.parse import urlparse; print(urlparse('${DB_URL}').port)")

# --- Drop the database (using local superuser for admin ops) ---
echo "==> Dropping database: $DB_NAME"
dropdb -h "$DB_HOST" -p "$DB_PORT" -U postgres --if-exists "$DB_NAME"

# --- Remove .env ---
echo "==> Removing .env"
rm -f "$WORKTREE_DIR/.env"

echo "==> Teardown complete!"
