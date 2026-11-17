## Этап сборки зависимостей (builder)
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.3.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry==$POETRY_VERSION

WORKDIR /app

# Копируем только файлы для установки зависимостей (кэширование слоев)
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости (без dev и lint)
RUN poetry install --without dev --without lint --no-root --no-interaction --no-ansi

## Финальный образ
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем установленные пакеты из builder-образа
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код
COPY src/ ./src/
COPY cli.py ./

# Указываем точку входа для CLI
ENTRYPOINT ["python", "-m", "cli"]
CMD ["run", "--file", "data/operations.xlsx"]
