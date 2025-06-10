# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from app.main import create_app


# NOTE(willkg): this allows us to wrap the app in middleware later
wsgi_app = create_app()
