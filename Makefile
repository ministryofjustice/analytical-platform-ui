#!make

build-static:
	make build-css
	make build-js

build-css:
	mkdir -p static/assets/fonts
	mkdir -p static/assets/images
	cp -R node_modules/govuk-frontend/govuk/assets/fonts/. static/assets/fonts
	cp -R node_modules/govuk-frontend/govuk/assets/images/. static/assets/images
	npm run css

build-js:
	mkdir -p static/assets/js
	cp node_modules/govuk-frontend/govuk/all.js static/assets/js/govuk.js

db-migrate:
	python manage.py migrate

db-drop:
	python manage.py reset_db

serve:
	python manage.py runserver

serve-sso:
	aws-sso exec --profile analytical-platform-development:AdministratorAccess -- python manage.py runserver

container:
	docker build -t controlpanel .

test: container
	@echo
	@echo "> Running Python Tests (In Docker)..."
	IMAGE_TAG=controlpanel docker compose --file=contrib/docker-compose-test.yml run --rm interfaces
