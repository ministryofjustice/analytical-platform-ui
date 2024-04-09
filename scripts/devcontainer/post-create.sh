#!/usr/bin/env bash

# Upgrade NPM
npm install --global npm@latest

# Start Postgres
docker compose --file contrib/docker-compose-postgres.yml up --detach

# Upgrade Pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.dev.txt

# install npm dependencies and static assets
npm install
make build-static

# Run migrations
python manage.py migrate
