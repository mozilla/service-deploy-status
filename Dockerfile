FROM python:3.13.4-slim-bullseye@sha256:de0e7494b82e073b7586bfb2b081428ca2c8d1db2f6a6c94bc2e4c9bd4e71276 AS app_base

# Set up user and group
ARG groupid=10001
ARG userid=10001

RUN groupadd --gid $groupid app \
  && useradd -g app --uid $userid --shell /usr/sbin/nologin --create-home app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.12@sha256:4faec156e35a5f345d57804d8858c6ba1cf6352ce5f4bffc11b7fdebdef46a38 /uv /usr/local/bin/

# Set environment variables
ENV UV_PROJECT_ENVIRONMENT=/venv \
    UV_NO_MANAGED_PYTHON=1 \
    UV_PYTHON_DOWNLOADS=never \
    VIRTUAL_ENV=/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/app/.cache/uv \
    UV_FROZEN=1 \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1 \
    PYTHONUNBUFFERED=True \
    PYTHONPATH=/app \
    APP_HOME=/app \
    PATH="/venv/bin:$PATH"

# Install dependencies
RUN --mount=type=cache,target=/app/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv venv $VIRTUAL_ENV && \
    uv sync --no-install-project --no-editable

# Set working directory
WORKDIR $APP_HOME

RUN chown -R app:app $APP_HOME

USER app

# Copy local code to the container image
COPY --chown=app:app . $APP_HOME

# Now create the final context that runs the web api
FROM app_base AS web_api

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["web"]
