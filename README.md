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
  SYSTEM NAME:                           - the name of the system of services
    - name: SERVICE NAME                 - the name of a single service in the system
      description: SERVICE DESCRIPTION   - short description of service
      environments:
        - name: ENVIRONMENT NAME         - name of an environment
          host: ENVIRONMENT HOST         - host for this environment with a /__version__
```
If you want to add a system or update an existing system, submit a pull
request.
