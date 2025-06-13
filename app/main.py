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
import yaml

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
def get_systems_data():
    # NOTE(willkg): relative to repository root
    with open("app/systems.yaml", "rb") as fp:
        data = yaml.safe_load(fp)

    return data


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
        systems = list(sorted(systems_data["systems"].keys()))
        return render_template("index.html", systems=systems)

    @app.route("/system/<system>", methods=["GET"])
    @log_render_time
    def system_page(system):
        systems_data = get_systems_data()
        if system not in systems_data["systems"]:
            abort(404)

        output = []
        for service in systems_data["systems"][system]:
            output.append(f"{service['name']}: {service.get('description', '--')}")

            environments = service["environments"]

            for environment in environments:
                env_name = environment["name"]
                env_host = environment["host"]
                output.append(f"  {env_name}: {env_host}")
                host_version = fetch(f"{env_host}/__version__")

                source = host_version["source"]
                commit = host_version["commit"]
                tag = host_version.get("version") or "(none)"
                parsed = urlparse(source)
                _, user, repo = parsed.path.split("/")

                output.append(f"  {repo}  {commit}  {tag}")

                history = fetch_history_from_github(user, repo, commit)
                if history["total_commits"] == 0:
                    output.append("  status: up-to-date")

                else:
                    output.append(f"  status: {history['total_commits']} commits")
                    output.append("")
                    output.append(
                        f"  https://github.com/{user}/{repo}/compare/{commit[:8]}...main"
                    )
                    output.append("")

                    for i, commit_data in enumerate(history["commits"]):
                        if len(commit_data["parents"]) > 1:
                            # Skip merge commits
                            continue

                        output.append(
                            "  "
                            + commit_data["sha"][:8]
                            + " "
                            + ("HEAD: " if i == 0 else "")
                            + commit_data["commit"]["message"].splitlines()[0][:60]
                            + " "
                            + "("
                            + (commit_data["author"] or {}).get("login", "?")[:10]
                            + ")"
                        )

                output.append("")
            output.append("")

        return render_template("system.html", system=system, output="\n".join(output))

    return app
