#!/usr/bin/env bash
set -euxo pipefail

# Run pre-commit
UV_PROJECT_ENVIRONMENT=/home/vscode/.venv uv run pre-commit install
