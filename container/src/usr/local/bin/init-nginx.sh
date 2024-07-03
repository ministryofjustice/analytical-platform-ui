#!/usr/bin/env sh

# This is a helper script used in Analytical Platform UI's Kubernetes deployment
# It copies the static assets into a shared volume for the NGINX container to serve

export STATIC_SRC="${STATIC_SRC:-"/ap/static"}"
export STATIC_DEST="${STATIC_DEST:-"/staticfiles"}"

cp -R "${STATIC_SRC}" "${STATIC_DEST}"
