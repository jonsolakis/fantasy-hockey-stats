FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base AS development

ENV PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md alembic.ini ./
COPY backend ./backend
RUN pip install -e '.[dev]'

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

COPY pyproject.toml README.md alembic.ini ./
COPY backend ./backend
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
