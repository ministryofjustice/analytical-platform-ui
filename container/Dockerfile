##################################################
# Stage: build-node
# From: public.ecr.aws/docker/library/node:22.9.0
##################################################
FROM public.ecr.aws/docker/library/node:22.9.0 AS build-node

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
FROM ghcr.io/astral-sh/uv:python3.13-alpine@sha256:30b0d0f67eb7a5f79325709fff1bb0a93c991674b0caf04ef4017e7ee5b44be4 AS build-python

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE="copy"

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
<<EOF
uv sync --locked --no-install-project --no-editable
EOF

##################################################
# Stage: final
# From: docker.io/python:3.13-alpine3.22
##################################################
FROM docker.io/python:3.13-alpine3.22@sha256:f196fd275fdad7287ccb4b0a85c2e402bb8c794d205cf6158909041c1ee9f38d AS final

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
