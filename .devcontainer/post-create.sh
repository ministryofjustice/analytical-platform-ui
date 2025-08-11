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
uv run python manage.py migrate --noinput

# Install npm dependencies and static assets
npm install
make build-static

# Create aws and kube configs
aws-sso login
aws-sso setup profiles --force

aws-sso exec --profile analytical-platform-compute-development:modernisation-platform-sandbox -- aws eks --region eu-west-2 update-kubeconfig --name analytical-platform-compute-development --alias analytical-platform-compute-development
kubectl config use-context analytical-platform-compute-development
