# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Sets the opentelemetry collector endpoint
    APP_OTEL_COLLECTOR_ENDPOINT: str = "localhost:4317"

    # "local", "stage", or "prod"
    APP_ENVIRONMENT: str = "local"

    # "INFO" or "WARNING"
    APP_LOGGING_LEVEL: str = "INFO"

    # APP_DEBUG sets Flask's DEBUG variable; DON'T set this in server environments.
    # https://flask.palletsprojects.com/en/stable/config/#DEBUG
    DEBUG: bool = Field(alias="APP_DEBUG", default=False)


settings = Settings()
