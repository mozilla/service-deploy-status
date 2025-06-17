# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import functools
import json
import logging
import os
import requests
import time
from urllib.parse import urlparse

from flask import abort, Flask, jsonify, render_template

from app.libsystems import get_systems_data
from app.observability import log_settings, setup_logging
from app.settings import settings


def fetch(url):
    resp = requests.get(url)
    # FIXME(willkg): handle 429s, retrying, and other response codes
    resp.raise_for_status()
    return resp.json()


def fetch_history_from_github(user, repo, from_sha):
    url = f"https://api.github.com/repos/{user}/{repo}/compare/{from_sha}...main"
    resp = requests.get(url)
    # FIXME(willkg): handle 429s, retrying, and other response codes
    resp.raise_for_status()
    return resp.json()


def log_render_time(fun):
    fun_name = fun.__name__
    logger = logging.getLogger(__name__)

    @functools.wraps(fun)
    def _log_render_time(*args, **kwargs):
        start_time = time.time()
        status_code = 0
        try:
            ret = fun(*args, **kwargs)
            if isinstance(ret, str):
                status_code = 200
            elif isinstance(ret, tuple) and isinstance(ret[1], int):
                status_code = ret[1]
            else:
                logger.info("unknown return type: %s %s", type(ret), repr(ret)[:20])
            return ret
        except Exception as exc:
            if hasattr(exc, "code"):
                status_code = exc.code
            else:
                status_code = 500
            raise exc

        finally:
            logger.info(
                "%s (%s) render time: %s",
                fun_name,
                status_code,
                f"{time.time() - start_time:0.03f}s",
            )

    return _log_render_time


@functools.cache
def get_version():
    if os.path.exists("version.json"):
        with open("version.json", "rb") as fp:
            data = json.load(fp)
    else:
        data = {
            "source": "https://github.com/mozilla/service-deploy-status",
            "version": "",
            "commit": "",
            "build": "",
        }
    return data


def create_app(settings_overrides=None):
    app = Flask(__name__)
    app.config.from_object("app.settings.settings")

    if settings_overrides:
        app.config.update(settings_overrides)

    setup_logging(
        env=settings.APP_ENVIRONMENT, logging_level=settings.APP_LOGGING_LEVEL
    )

    log_settings(app)

    @app.route("/__heartbeat__", methods=["GET"])
    @log_render_time
    def dockerflow_heartbeat():
        # Check GitHub status and return whether GitHub is up or not
        resp = requests.get("https://www.githubstatus.com/api/v2/status.json")
        if resp.status_code != 200:
            return jsonify({"github": resp.status_code}), 500
        data = resp.json()
        if data["status"]["indicator"] != "none":
            return jsonify({"github": data["status"]["indicator"]}), 500

        return jsonify({"github": "ok"}), 200

    @app.route("/__lbheartbeat__", methods=["GET"])
    @log_render_time
    def dockerflow_lbheartbeat():
        # Returns an HTTP 200 with an empty response
        return "{}"

    @app.route("/__version__", methods=["GET"])
    @log_render_time
    def dockerflow_version():
        return jsonify(get_version()), 200

    @app.route("/", methods=["GET"])
    @log_render_time
    def index_page():
        systems_data = get_systems_data()
        systems = list(sorted(systems_data.systems.keys()))
        return render_template("index.html", systems=systems)

    @app.route("/system/<system>", methods=["GET"])
    @log_render_time
    def system_page(system):
        systems_data = get_systems_data()
        if system not in systems_data.systems:
            abort(404)

        data = []
        for service in systems_data.systems[system].services:
            service_data = {
                "name": service.name,
                "description": service.description or "--",
            }

            environments_data = []
            for environment in service.environments:
                environment_data = {
                    "name": environment.name,
                    "host": environment.host,
                }

                host_version = fetch(f"{environment.host}/__version__")
                environment_data["commit"] = host_version["commit"]
                environment_data["source"] = host_version["source"]
                environment_data["tag"] = host_version.get("version") or "(none)"
                parsed = urlparse(environment_data["source"])
                _, user, repo = parsed.path.split("/")

                environment_data["user"] = user
                environment_data["repo"] = repo

                history = fetch_history_from_github(
                    user=user,
                    repo=repo,
                    from_sha=environment_data["commit"],
                )
                if history["total_commits"] == 0:
                    environment_data["status"] = "up-to-date"
                    environment_data["commits"] = []

                else:
                    environment_data["status"] = f"{history['total_commits']} commits"
                    # output.append(
                    #     f"  https://github.com/{user}/{repo}/compare/{commit[:8]}...main"
                    # )

                    commit_data = []
                    for i, commit in enumerate(history["commits"]):
                        if len(commit["parents"]) > 1:
                            # Skip merge commits
                            continue

                        commit_data.append(
                            {
                                "sha": commit["sha"],
                                "is_head": i == 0,
                                "message": commit["commit"]["message"].splitlines()[0],
                                "author": (commit["author"] or {}).get("login", "?"),
                            }
                        )
                    environment_data["commits"] = commit_data
                environments_data.append(environment_data)
            service_data["environments"] = environments_data
            data.append(service_data)

        return render_template("system.html", system=system, data=data)

    return app

    @app.route("/throw_error", methods=["GET"])
    @log_render_time
    def throw_error_page():
        raise Exception("Intentional unhandled exception")
