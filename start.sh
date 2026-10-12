#!/bin/bash
# One-command startup for HMS Enterprise after a machine restart.
# Starts the embedded PostgreSQL (as the unprivileged 'nobody' user, since
# postgres refuses to run as root), then launches the Django dev server.
# Must be run as root (the environment's default).
set -e
PROJECT=/home/hatch/workspace/hms-enterprise
cd "$PROJECT"

echo "==> starting PostgreSQL..."
setpriv --reuid=65534 --regid=65534 --clear-groups \
    "$PROJECT/.venv/bin/python" "$PROJECT/scripts/db.py" start

echo "==> starting HMS Enterprise on http://127.0.0.1:8000 ..."
exec "$PROJECT/.venv/bin/python" manage.py runserver 127.0.0.1:8000
