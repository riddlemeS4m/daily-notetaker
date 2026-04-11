#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
set -a
source .env
set +a

# Generate a Procfile with worktree-specific ports resolved from .env
python3 -c "
import os

port = os.environ.get('PORT', '8000')
flower_port = os.environ.get('FLOWER_PORT', '5555')

with open('Procfile.dev') as f:
    content = f.read()

content = content.replace(':8000', ':' + port).replace(':5555', ':' + flower_port)

with open('.superset/Procfile.resolved', 'w') as f:
    f.write(content)
"

echo "==> Starting on port $PORT (flower on $FLOWER_PORT)"
honcho start -f .superset/Procfile.resolved web worker beat flower
