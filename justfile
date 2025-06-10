_default:
    @just --list

_env:
    #!/usr/bin/env sh
    if [ ! -f .env ]; then
        echo "Copying env.dist to .env..."
        cp env.dist .env
    fi

build: _env
    docker compose build --progress plain

run: _env build
    docker compose up --watch web

shell: _env build
    docker compose run --rm web shell

lint: _env build
    docker compose run --rm web shell ruff format --check
    docker compose run --rm web shell ruff check

format: _env build
    # NOTE(willkg): this runs in a utility service which volume-mounts the
    # codebase so it can make changes
    docker compose run --rm utility shell ruff format /app_code

test: _env build
    docker compose run --rm web shell pytest tests/
