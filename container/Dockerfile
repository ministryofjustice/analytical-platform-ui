##### BUILD

FROM public.ecr.aws/docker/library/node:23.1.0 AS build-node

WORKDIR /build

COPY package.json package-lock.json ./
COPY assets/scss/app.scss ./assets/scss/app.scss

RUN <<EOF
npm install

npm run css
EOF

##### FINAL

FROM public.ecr.aws/docker/library/python:3.12.5-alpine3.20

LABEL org.opencontainers.image.vendor="Ministry of Justice" \
      org.opencontainers.image.authors="Analytical Platform (analytical-platform@digital.justice.gov.uk)" \
      org.opencontainers.image.title="Analytical Platform UI" \
      org.opencontainers.image.description="UI for Analytical Platform" \
      org.opencontainers.image.url="https://github.com/ministryofjustice/analytical-platform-ui"

ENV CONTAINER_USER="analyticalplatform" \
    CONTAINER_UID="1000" \
    CONTAINER_GROUP="analyticalplatform" \
    CONTAINER_GID="1000" \
    APP_ROOT="/app"

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

# Install APK packages
RUN <<EOF
apk add --no-cache --virtual .build-deps \
  libffi-dev=3.4.6-r0 \
  gcc=13.2.1_git20240309-r0 \
  musl-dev=1.2.5-r0 \

apk add --no-cache \
  libpq-dev=16.3-r0
EOF

# Install Python packages and remove APK build dependencies
COPY requirements.txt /tmp/requirements.txt
RUN <<EOF
pip install --no-cache-dir --requirement /tmp/requirements.txt

apk del .build-deps
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

# Set user and working directory
USER ${CONTAINER_USER}
WORKDIR ${APP_ROOT}

# Collect static files
RUN <<EOF
python manage.py collectstatic --noinput --ignore=*.scss
EOF

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD ["/usr/local/bin/healthcheck.sh"]
