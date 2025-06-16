# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json

import pytest

from app import main
from app.libsystems import Systems


def test_index_page(client, caplog):
    resp = client.get("/")
    assert resp.status_code == 200

    # Verify that one of the systems in app/systems.toml is in the output
    assert b"socorro" in resp.data

    # Verify the render time was logged
    records = [
        record.message
        for record in caplog.records
        if record.message.startswith("index_page (200) render time")
    ]
    assert len(records) == 1


def test_dockerflow_heartbeat(client, responses):
    responses.get(
        "https://www.githubstatus.com/api/v2/status.json",
        status=200,
        content_type="application/json; charset-utf-8",
        body=json.dumps(
            {
                "page": {
                    "id": "kctbh9vrtdwd",
                    "name": "GitHub",
                    "url": "https://www.githubstatus.com",
                    "time_zone": "Etc/UTC",
                    "updated_at": "2025-06-10T18:23:50.967Z",
                },
                "status": {
                    "indicator": "none",
                    "description": "All Systems Operational",
                },
            }
        ),
    )

    resp = client.get("/__heartbeat__")
    assert resp.status_code == 200
    assert resp.data == b'{"github":"ok"}\n'


def test_dockerflow_lbheartbeat(client):
    resp = client.get("/__lbheartbeat__")
    assert resp.status_code == 200
    assert resp.data == b"{}"


def test_dockerflow_version(client):
    resp = client.get("/__version__")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    # NOTE(willkg): we test that it has the right keys, but not the actual contents
    # since we don't know if it's running in a local dev environment or in CI
    assert list(sorted(data.keys())) == ["build", "commit", "source", "version"]


@pytest.fixture()
def fake_systems_data(monkeypatch, responses):
    def get_systems_data_mock():
        return Systems.model_validate(
            {
                "systems": {
                    "exampleapp": {
                        "services": [
                            {
                                "name": "Service 1",
                                "environments": [
                                    {
                                        "name": "stage",
                                        "host": "http://service1-stage.example.com",
                                    },
                                    {
                                        "name": "prod",
                                        "host": "http://service1.example.com",
                                    },
                                ],
                            },
                        ],
                    },
                },
            }
        )

    monkeypatch.setattr(main, "get_systems_data", get_systems_data_mock)

    # Stage is up-to-date
    responses.get(
        "http://service1-stage.example.com/__version__",
        status=200,
        content_type="application/json; charset-utf-8",
        body=json.dumps(
            {
                "source": "https://github.com/example/service1",
                "version": "main",
                "commit": "aaaaa12345",
                "build": "https://github.com/example/service1/actions/runs/15888888542",
            }
        ),
    )
    responses.get(
        "https://api.github.com/repos/example/service1/compare/aaaaa12345...main",
        status=200,
        content_type="application/json",
        body=json.dumps(
            {
                "total_commits": 0,
            }
        ),
    )

    # Prod is a couple of commits behind
    responses.get(
        "http://service1.example.com/__version__",
        status=200,
        content_type="application/json",
        body=json.dumps(
            {
                "source": "https://github.com/example/service1",
                "version": "v2025.06.10",
                "commit": "bbbbb12345",
                "build": "https://github.com/example/service1/actions/runs/15555555542",
            }
        ),
    )
    responses.get(
        "https://api.github.com/repos/example/service1/compare/bbbbb12345...main",
        status=200,
        content_type="application/json",
        body=json.dumps(
            {
                "total_commits": 2,
                "commits": [
                    {
                        "sha": "ee46327ef8dc59347749b06c60aed07730ed58aa",
                        "parents": [
                            # NOTE(willkg): service-deploy-status only looks at the
                            # number of parents--it doesn't look at the data
                            {},
                        ],
                        "commit": {
                            "message": (
                                "chore: updated csp dependency\n\n"
                                "This version of csp fixes bug 111111."
                            ),
                        },
                        "author": {
                            "login": "willkg",
                        },
                    },
                    {
                        "sha": "ddb3277c7e6365ac28c61cef8f25c3e295e6329a",
                        "parents": [
                            # NOTE(willkg): service-deploy-status only looks at the
                            # number of parents--it doesn't look at the data
                            {},
                        ],
                        "commit": {
                            "message": "chore: update README",
                        },
                        "author": {
                            "login": "willkg",
                        },
                    },
                ],
            }
        ),
    )


def test_system_page(client, responses, fake_systems_data):
    resp = client.get("/system/exampleapp")
    assert resp.status_code == 200

    # It produces a lot of output, so we're going to test for the existence of some
    # strings and then call it a day.
    for expected_string in [
        (
            b'stage: <a href="http://service1-stage.example.com">'
            + b"http://service1-stage.example.com</a>"
        ),
        (
            b'<a href="https://github.com/example/service1/commit/aaaaa12345">'
            + b"aaaaa12345</a> | main"
        ),
        b"status: up-to-date",
        b"status: 2 commits",
        (
            b'<a href="https://github.com/example/service1/commit/'
            + b'ee46327ef8dc59347749b06c60aed07730ed58aa">'
            + b"ee46327ef8dc59347749b06c60aed07730ed58aa</a>"
        ),
        b"chore: updated csp dependency",
    ]:
        assert expected_string in resp.data


def test_system_page_bad_system(client, responses, fake_systems_data, caplog):
    # NOTE(willkg): we want to use the fake system data, but we don't want to enforce
    # that all responses are matched, so we remove the expected responses.
    responses.reset()

    resp = client.get("/system/badvalue")
    assert resp.status_code == 404

    # Verify the render time was logged
    records = [
        record.message
        for record in caplog.records
        if record.message.startswith("system_page (404) render time")
    ]
    assert len(records) == 1
