#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Default variables
: "${PORT:=8000}"
: "${APP_GUNICORN_TIMEOUT:=300}"
: "${APP_WAITRESS_TIMEOUT:=300}"

(set -o posix; set) | grep APP_WAITRESS

cd /app/

exec uv run waitress-serve \
    --port=${PORT} \
    --threads=1 \
    --channel-timeout="${APP_WAITRESS_TIMEOUT}" \
    app.wsgi:wsgi_app
