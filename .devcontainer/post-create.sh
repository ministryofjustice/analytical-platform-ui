#!/usr/bin/env bash
set -euxo pipefail

# Upgrade NPM
npm install --global npm@latest

# Start Postgres
docker compose --file contrib/docker-compose-postgres.yml up --detach

# Install venv, dependencies and run migrations. Store venv outside /workspaces for better performance
rm -rf /home/vscode/.venv
uv venv
uv sync
uv run python manage.py migrate --noinput --settings=ap.settings.local

# Install npm dependencies and static assets
npm install
make build-static

# Create aws and kube configs
aws-sso login
aws-sso setup profiles --force
