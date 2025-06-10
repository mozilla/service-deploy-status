FROM python:3.13.4-slim-bullseye@sha256:de0e7494b82e073b7586bfb2b081428ca2c8d1db2f6a6c94bc2e4c9bd4e71276 AS app_base

# Set up user and group
ARG groupid=10001
ARG userid=10001

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.7.12@sha256:4faec156e35a5f345d57804d8858c6ba1cf6352ce5f4bffc11b7fdebdef46a38 /uv /uvx /bin/

# Set environment variables
ENV PYTHONUNBUFFERED=True \
    PYTHONPATH=/app \
    UV_COMPILE_BYTECODE=1 \
    APP_HOME=/app

RUN groupadd --gid $groupid app \
  && useradd -g app --uid $userid --shell /usr/sbin/nologin --create-home app

# Set working directory
WORKDIR $APP_HOME

RUN chown -R app:app $APP_HOME

USER app

# Install dependencies as root
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-managed-python --no-install-project

# Copy local code to the container image
COPY --chown=app:app . $APP_HOME

# Set the PATH environment variable
ENV PATH="$APP_HOME/.venv/bin:$PATH"

# Now create the final context that runs the web api
FROM app_base AS web_api

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["web"]
