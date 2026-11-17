FROM public.ecr.aws/docker/library/python:3.14.10-slim-bookworm@sha256:1faf2343e747208b2a36e5f2b5ff908ec3b2d0078a6a7bfe73b535698fe83909 AS builder
RUN pip install --no-cache-dir uv==0.11.32
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev

FROM public.ecr.aws/docker/library/python:3.14.10-slim-bookworm@sha256:1faf2343e747208b2a36e5f2b5ff908ec3b2d0078a6a7bfe73b535698fe83909 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --uid 10001 --create-home invest
COPY --from=builder /app/.venv /app/.venv
COPY backend/ ./
COPY contracts/ /contracts/
USER invest
CMD ["/app/.venv/bin/gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "--error-logfile", "-"]

FROM builder AS test-deps
RUN uv sync --locked
FROM runtime AS test
COPY --from=test-deps /app/.venv /app/.venv
