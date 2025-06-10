#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Default variables
: "${PORT:=8000}"
: "${APP_GUNICORN_WORKERS:=1}"
: "${APP_GUNICORN_TIMEOUT:=300}"
: "${APP_GUNICORN_MAX_REQUESTS:=0}"
: "${APP_GUNICORN_MAX_REQUESTS_JITTER:=0}"

(set -o posix; set) | grep APP_GUNICORN

cd /app/

exec uv run --no-project gunicorn \
    --bind 0.0.0.0:"${PORT}" \
    --timeout "${APP_GUNICORN_TIMEOUT}" \
    --workers "${APP_GUNICORN_WORKERS}" \
    --max-requests="${APP_GUNICORN_MAX_REQUESTS}" \
    --max-requests-jitter="${APP_GUNICORN_MAX_REQUESTS_JITTER}" \
    --access-logfile - \
    app.wsgi:wsgi_app
