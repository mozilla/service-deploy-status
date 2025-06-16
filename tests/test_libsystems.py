# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from app.libsystems import Systems


def test_empty():
    Systems.model_validate({"systems": {}})


def test_system_with_no_services():
    Systems.model_validate({"systems": {"examplesystem": {"services": []}}})
