FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Infisical CLI: the entrypoint pulls runtime secrets using a least-privilege
# machine identity delivered by CI, so no credentials are baked into the image.
RUN apt-get update \
  && apt-get install -y --no-install-recommends curl bash ca-certificates jq \
  && curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' | bash \
  && apt-get update \
  && apt-get install -y --no-install-recommends infisical \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (cached layer). Build context is the repo root.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application logic into the image.
COPY backend/ ./
COPY config/prod/backend.json ./config.json

ENV APP_ENV=prod

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
