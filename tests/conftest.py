# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest

from app.main import create_app


@pytest.fixture()
def app():
    app = create_app(settings_overrides={"TESTING": True})
    app.config.update(
        {
            "APP_ENVIRONMENT": "test",
        }
    )

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
