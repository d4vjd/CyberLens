# CyberLens SIEM — Copyright (c) 2026 David Pupăză
# Licensed under the Hippocratic License 3.0. See LICENSE file for details.

FROM python:3.12-slim

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/README.md backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/src ./src
COPY rules /app/rules
COPY playbooks /app/playbooks

RUN pip install --upgrade pip \
    && pip install .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn cyberlens.main:app --host 0.0.0.0 --port 8000"]