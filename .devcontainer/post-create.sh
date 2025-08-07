#!/usr/bin/env bash
set -euxo pipefail

# Upgrade NPM
npm install --global npm@latest

# Start Postgres
docker compose --file contrib/docker-compose-postgres.yml up --detach

# Remove existing virtual environment
rm -rf .venv

# Install venv, dependencies and run migrations
uv sync
uv run python manage.py migrate

# # install npm dependencies and static assets
npm install
make build-static

# # create aws and kube configs
aws-sso login
aws-sso exec --profile analytical-platform-compute-development:modernisation-platform-sandbox -- aws eks --region eu-west-2 update-kubeconfig --name analytical-platform-compute-development --alias apc-dev-cluster
kubectl config use-context apc-dev-cluster
