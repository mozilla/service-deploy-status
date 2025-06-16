# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import functools
import json

from pydantic import BaseModel
import yaml


class Environment(BaseModel):
    name: str
    host: str


class Service(BaseModel):
    name: str
    description: str | None = None
    environments: list[Environment]


class System(BaseModel):
    services: list[Service]


class Systems(BaseModel):
    systems: dict[str, System]


@functools.cache
def get_systems_data():
    # NOTE(willkg): relative to repository root
    with open("app/systems.yaml", "rb") as fp:
        data = yaml.safe_load(fp)

    return Systems.model_validate(data)


def print_schema():
    print(json.dumps(Systems.model_json_schema(), indent=2))
