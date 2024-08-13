#!/usr/bin/env bash

# Upgrade NPM
npm install --global npm@latest

# Start Postgres
docker compose --file contrib/docker-compose-postgres.yml up --detach

# Upgrade Pip
pip install --break-system-package --upgrade pip

# Install dependencies
pip install --break-system-package --requirement requirements.dev.txt

# install npm dependencies and static assets
npm install
make build-static

# Run migrations
python manage.py migrate

# create aws and kube configs
aws-sso config-profiles --force

aws-sso exec --profile analytical-platform-development:AdministratorAccess -- aws eks --region eu-west-1 update-kubeconfig --name development-aWrhyc0m --alias dev-eks-cluster
aws-sso exec --profile analytical-platform-compute-development:modernisation-platform-sandbox -- aws eks --region eu-west-2 update-kubeconfig --name analytical-platform-compute-development --alias apc-dev-cluster
kubectl config use-context dev-eks-cluster
