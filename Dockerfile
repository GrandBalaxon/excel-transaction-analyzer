## Dependency build stage (builder)
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry==$POETRY_VERSION

WORKDIR /app

# Copy only the dependency files first (layer caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies (without dev and lint groups)
RUN poetry install --without dev --without lint --no-root --no-interaction --no-ansi

## Final image
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy installed packages from the builder image
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the source code
COPY src/ ./src/
COPY cli.py ./

# Set the CLI entry point
ENTRYPOINT ["python", "-m", "cli"]
CMD ["run", "--file", "data/operations.xlsx"]
