#!/usr/bin/env bash
set -euxo pipefail

# Run pre-commit
uv run pre-commit install
