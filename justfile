_default:
    @just --list

_env:
    #!/usr/bin/env sh
    if [ ! -f .env ]; then
        echo "Copying env.dist to .env..."
        cp env.dist .env
    fi

# Build the Docker images
build: _env
    docker compose --progress plain build

# Run web service and backing services
run: _env build
    docker compose up --watch web

# Run a shell in the Docker web image
shell: _env build
    docker compose run --rm web shell

# Run tests
test: _env build
    docker compose run --rm web shell pytest tests/

# Lint code files
lint: _env build
    docker compose run --rm web shell ruff format --check
    docker compose run --rm web shell ruff check

# Re-format code files
format: _env build
    docker compose run --rm --volume=.:/app_code web shell ruff format /app_code

# List outdated dependencies
list-outdated: _env build
    docker compose run --rm web shell uv pip list --outdated

# Update uv.lock file
update-lock: _env build
    docker compose run --rm --volume=.:/app web shell uv lock --upgrade
