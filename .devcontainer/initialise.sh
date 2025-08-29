#!/usr/bin/env bash
set -euxo pipefail

if command -v op >/dev/null 2>&1; then
  op document get --vault "Analytical Platform" "Analytical Platform UI .env" --out-file .env
else
  echo "op command not found"
fi
