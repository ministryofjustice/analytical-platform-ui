#!/usr/bin/env bash

profileName=${@:1}
aws-sso exec --profile ${profileName} -- python manage.py runserver
