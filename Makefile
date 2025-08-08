#!make

CONTAINER_IMAGE_NAME ?= ghcr.io/ministryofjustice/analytical-platform-ui
CONTAINER_IMAGE_TAG  ?= local

build-static:
	make build-css
	make build-js

build-css:
	mkdir -p static/assets/fonts
	mkdir -p static/assets/images
	cp -R node_modules/govuk-frontend/dist/govuk/assets/fonts/. static/assets/fonts
	cp -R node_modules/govuk-frontend/dist/govuk/assets/images/. static/assets/images
	cp -R node_modules/@ministryofjustice/frontend/moj/assets/images/. static/assets/images
	npm run css

build-js:
	mkdir -p static/assets/js
	cp node_modules/govuk-frontend/dist/govuk/all.bundle.js static/assets/js/govuk.js
	cp node_modules/govuk-frontend/dist/govuk/all.bundle.js.map static/assets/js/govuk.js.map

db-migrate:
	python manage.py migrate

db-drop:
	python manage.py reset_db

serve:
	python manage.py runserver

serve-sso:
	aws-sso exec --profile analytical-platform-compute-development:platform-engineer-admin -- python manage.py runserver

container-build:
	@echo "Building container image $(CONTAINER_IMAGE_NAME):$(CONTAINER_IMAGE_TAG)"
	docker build --platform linux/amd64 --file Dockerfile --tag $(CONTAINER_IMAGE_NAME):$(CONTAINER_IMAGE_TAG) .

container-test: container-build
	@echo "Testing container image $(CONTAINER_IMAGE_NAME):$(CONTAINER_IMAGE_TAG)"
	container-structure-test test --platform linux/amd64 --config test/container-structure-test.yml --image $(CONTAINER_IMAGE_NAME):$(CONTAINER_IMAGE_TAG)

container-scan: container-test
	@echo "Scanning container image $(CONTAINER_IMAGE_NAME):$(CONTAINER_IMAGE_TAG) for vulnerabilities"
	trivy image --platform linux/amd64 --severity HIGH,CRITICAL $(CONTAINER_IMAGE_NAME):$(CONTAINER_IMAGE_TAG)

test: container-build
	@echo
	@echo "> Running Python Tests (In Docker)..."
	CONTAINER_IMAGE_NAME=$(CONTAINER_IMAGE_NAME) CONTAINER_IMAGE_TAG=$(CONTAINER_IMAGE_TAG) docker compose --file=contrib/docker-compose-test.yml run --rm interfaces

chart-lint:
	@echo "Linting Helm chart"
	ct lint --charts chart
