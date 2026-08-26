FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
      poppler-utils webp calibre && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV COOKS_LIBRARY_PATH=/library/existing:/library/incoming
ENV COOKS_DB_PATH=/data/cooks.db
ENV COOKS_DATA_DIR=/data
ENV COOKS_CATEGORIES_FILE=/data/categories.yml

CMD ["sh", "-c", "mkdir -p /data && [ -f /data/categories.yml ] || cp /app/categories.yml /data/categories.yml; exec uvicorn cooksLibrary.web.main:app --host 0.0.0.0 --port 8000"]