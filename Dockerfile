##################################################
# Stage: build-node
# From: docker.io/node:22.18.0-alpine3.22
##################################################
FROM docker.io/node:24.7.0-alpine3.22@sha256:be4d5e92ac68483ec71440bf5934865b4b7fcb93588f17a24d411d15f0204e4f AS build-node

WORKDIR /build

COPY package.json package-lock.json ./
COPY assets/scss/app.scss ./assets/scss/app.scss

RUN <<EOF
npm install

npm run css
EOF

##################################################
# Stage: build-python
# From: docker.io/python:3.13-alpine3.22
##################################################
FROM ghcr.io/astral-sh/uv:python3.13-alpine@sha256:9b0b40ee26d09b0ddb3b39f0aef24174f59f766af36591d541a2e14266a20886 AS build-python

ARG BUILD_DEV="false"

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE="copy"

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
<<EOF
if [[ "${BUILD_DEV}" == "true" ]]; then
  uv sync --locked --no-install-project --no-editable
else
  uv sync --locked --no-install-project --no-editable --no-dev
fi
EOF

##################################################
# Stage: final
# From: docker.io/python:3.13-alpine3.22
##################################################
FROM docker.io/python:3.13-alpine3.22@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844 AS final

LABEL org.opencontainers.image.vendor="Ministry of Justice" \
      org.opencontainers.image.authors="Analytical Platform (analytical-platform@digital.justice.gov.uk)" \
      org.opencontainers.image.title="Analytical Platform UI" \
      org.opencontainers.image.description="UI for Analytical Platform" \
      org.opencontainers.image.url="https://github.com/ministryofjustice/analytical-platform-ui"

ENV CONTAINER_USER="analyticalplatform" \
    CONTAINER_UID="1000" \
    CONTAINER_GROUP="analyticalplatform" \
    CONTAINER_GID="1000" \
    APP_ROOT="/app" \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"


# Configure user
RUN <<EOF
addgroup \
  --gid ${CONTAINER_GID} \
  --system \
  ${CONTAINER_GROUP}

adduser \
  --uid ${CONTAINER_UID} \
  --ingroup ${CONTAINER_GROUP} \
  --disabled-password \
  ${CONTAINER_USER}

install --directory --owner ${CONTAINER_USER} --group ${CONTAINER_GROUP} --mode 0755 \
  ${APP_ROOT} \
  ${APP_ROOT}/static/assets/fonts \
  ${APP_ROOT}/static/assets/images \
  ${APP_ROOT}/static/assets/js
EOF

# Copy compiled assets
COPY --from=build-node --chown=${CONTAINER_USER}:${CONTAINER_GROUP} /build/static/app.css ${APP_ROOT}/static/app.css
COPY --from=build-node --chown=${CONTAINER_USER}:${CONTAINER_GROUP} /build/node_modules/govuk-frontend/dist/govuk/assets/fonts/. ${APP_ROOT}/static/assets/fonts
COPY --from=build-node --chown=${CONTAINER_USER}:${CONTAINER_GROUP} /build/node_modules/govuk-frontend/dist/govuk/assets/images/. ${APP_ROOT}/static/assets/images
COPY --from=build-node --chown=${CONTAINER_USER}:${CONTAINER_GROUP} /build/node_modules/govuk-frontend/dist/govuk/all.bundle.js ${APP_ROOT}/static/assets/js/govuk.js

# Copy application code
COPY --chown=${CONTAINER_USER}:${CONTAINER_GROUP} manage.py ${APP_ROOT}/manage.py
COPY --chown=${CONTAINER_USER}:${CONTAINER_GROUP} ap ${APP_ROOT}/ap
COPY --chown=${CONTAINER_USER}:${CONTAINER_GROUP} templates ${APP_ROOT}/templates
COPY --chown=${CONTAINER_USER}:${CONTAINER_GROUP} tests ${APP_ROOT}/tests

# Copy container files
COPY --chown=nobody:nobody --chmod=0755 container/src/usr/local/bin/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chown=nobody:nobody --chmod=0755 container/src/usr/local/bin/healthcheck.sh /usr/local/bin/healthcheck.sh
COPY --chown=nobody:nobody --chmod=0755 container/src/usr/local/bin/init-nginx.sh /usr/local/bin/init-nginx.sh

# Set working directory
WORKDIR ${APP_ROOT}
COPY --from=build-python --chown=${CONTAINER_UID}:${CONTAINER_GID} /app/.venv /app/.venv

# Set user
USER ${CONTAINER_USER}


# Collect static files
RUN <<EOF
python manage.py collectstatic --noinput --ignore=*.scss
EOF

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD ["/usr/local/bin/healthcheck.sh"]
