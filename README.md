# README

This service lists systems specified in a configuration file and their deploy
status.

* License: MPLv2; see `LICENSE`
* Reporting issues: https://github.com/mozilla/service-deploy-status/issues
* Code of Conduct: See `CODE_OF_CONDUCT.md`
* Contributing: See `CONTRIBUTING`

# systems.yaml

The site is configured by a single `app/systems.yaml` file. It has this
structure:

```
systems:
  SYSTEM NAME:                             - the name of the system of services
    services:
      - name: SERVICE NAME                 - the name of a single service in the system
        description: SERVICE DESCRIPTION   - short description of service
        environments:
          - name: ENVIRONMENT NAME         - name of an environment
            host: ENVIRONMENT HOST         - host for this environment with a /__version__
```

If you want to add a system or update an existing system, submit a pull
request.

# development

Run `just` to list justfile recipes.

`just build` -- builds the service-deploy-status docker image

`just format` -- formats Python code

`just lint` -- lints Python code

`just test` -- runs Python tests

`just run` -- runs the service-deploy-status service in your local dev
environment

`just loadtest` -- runs the load tests against a service-deploy-status service
running in your local dev environment

To run load tests against the service running somewhere else, do:

```
docker run --rm -i \
    --volume $(pwd)/k6-scripts:/scripts \
    loadimpact/k6 run \
    --vus 2 \                                # <-- change number of virtual users here
    --duration 20s \                         # <-- change duration in seconds here
    --env BASEURL=http://web:8000 \          # <-- change the baseurl here
    /scripts/script.js
```
