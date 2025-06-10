# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import requests
import tomllib
from urllib.parse import urlparse

from flask import abort, Flask, render_template


app = Flask(__name__)


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


def get_systems_data():
    # NOTE(willkg): relative to repository root
    with open("app/systems.toml", "rb") as fp:
        data = tomllib.load(fp)

    return data


@app.route("/", methods=["GET"])
def index_page():
    systems_data = get_systems_data()
    systems = list(sorted(systems_data.keys()))
    return render_template("index.html", systems=systems)


@app.route("/system/<system>", methods=["GET"])
def system_page(system):
    systems_data = get_systems_data()
    if system not in systems_data:
        abort(404)

    system_data = systems_data[system]
    print(system_data)

    output = []
    for service_name, service in system_data.items():
        output.append(f"{service_name}: {service.get('name', '')}")

        environments = [
            key.split("_")[1]
            for key in service.keys()
            if key.startswith("environment_")
        ]

        for env_name in environments:
            host = service[f"environment_{env_name}"].rstrip("/")
            output.append(f"  {env_name}: {host}")
            host_version = fetch(f"{host}/__version__")

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

    # Generate the data structure to show in the system page

    return render_template("system.html", system=system, output="\n".join(output))
