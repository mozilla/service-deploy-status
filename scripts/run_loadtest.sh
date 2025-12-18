#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Runs a loadtest against specified baseurl
#
# Examples:
#
# ./scripts/run_loadtest.sh
# BASEURL=https://example.com/ ./scripts/run_loadtest.sh

: "${BASEURL:=http://web:8000}"

docker run --rm -i \
    --network service-deploy-status_default \
    --volume $(pwd)/k6-scripts:/scripts \
    loadimpact/k6 run \
    --vus 3 \
    --duration 300s \
    --env BASEURL="${BASEURL}" \
    /scripts/script.js
