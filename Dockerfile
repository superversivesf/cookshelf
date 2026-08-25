FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
      poppler-utils webp curl && \
    rm -rf /var/lib/apt/lists/*

# Download Tailwind standalone binary
RUN curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
    && chmod +x tailwindcss-linux-x64 \
    && mv tailwindcss-linux-x64 /usr/local/bin/tailwindcss

WORKDIR /app
ENV PYTHONPATH=/app/src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN tailwindcss -i src/cooksLibrary/web/static/css/input.css \
                -o src/cooksLibrary/web/static/css/app.css --minify

ENV COOKS_LIBRARY_PATH=/library/existing:/library/incoming
ENV COOKS_DB_PATH=/data/cooks.db
ENV COOKS_DATA_DIR=/data
ENV COOKS_CATEGORIES_FILE=/data/categories.yml

CMD ["sh", "-c", "mkdir -p /data && [ -f /data/categories.yml ] || cp /app/categories.yml /data/categories.yml; exec uvicorn cooksLibrary.web.main:app --host 0.0.0.0 --port 8000"]