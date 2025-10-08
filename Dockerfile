# builder stage
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.6 /uv /uvx /bin/

WORKDIR /app

ENV UV_CACHE_DIR=/app/.cache/uv
ENV XDG_DATA_HOME=/app/.local/share

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

RUN uv sync

# runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app"

COPY --from=builder /app/.venv /app/.venv

COPY ./src src

ENTRYPOINT ["python"]