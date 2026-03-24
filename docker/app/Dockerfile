# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml readme.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

EXPOSE 8000
CMD ["uvicorn", "fastai.app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
