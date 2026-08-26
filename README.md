# Cookshelf

A self-hosted web app for browsing, searching, and bookmarking recipes extracted from your collection of cookbook PDFs. Point it at a directory of PDF cookbooks, run the ingest pipeline, and get a searchable, mobile-friendly recipe library accessible from any device on your LAN.

## What It Does

- **Ingests** cookbook PDFs — extracts recipes using PDF outlines (bookmarks) or page-walk heuristics when outlines aren't available
- **Parses** ingredient lines into structured data (quantity, unit, ingredient, notes) with a regex-based parser that handles Unicode fractions, dual-unit suffixes, and section headers
- **Searches** across all recipes with SQLite FTS5 full-text search — search by title, description, instructions, or ingredient names
- **Browses** by book (with cover images), by category (content-derived), or by ingredient
- **Bookmarks** recipes to a Saved list
- **Tracks** recipes you've made with a date stamp — the Made list sorts by most recent
- **Renders** original PDF pages as fallback for recipes that couldn't be fully parsed
- **Lazy-renders** page images as WebP on first view, cached for subsequent access

## Tech Stack

- Python 3.12, FastAPI, Jinja2, HTMX
- Bootstrap 5 (via CDN, no build step)
- SQLite with FTS5 full-text search
- pypdf, pdfplumber, poppler-utils (pdftotext, pdftoppm), libwebp (cwebp)
- Docker

## Quick Start

### Requirements

- Docker and Docker Compose
- A directory of cookbook PDFs (text-based, not scanned images)

### Setup

1. Clone the repo:

```bash
git clone https://github.com/jasonrennie/cookshelf.git
cd cookshelf
```

2. Edit `docker-compose.yml` and replace `/path/to/your/cookbooks` with the path to your PDF collection:

```yaml
volumes:
  - /path/to/your/cookbooks:/library/existing:ro
  - ./incoming:/library/incoming
  - cooks-data:/data
```

3. Build and start:

```bash
docker compose up -d --build
```

4. Ingest your cookbooks (run once, or after adding new PDFs):

```bash
docker compose exec cookshelf python -m cooksLibrary.ingest
```

5. Open `http://localhost:8765` in your browser.

### Adding New PDFs

Drop new PDF files into the `incoming/` directory, then re-run the ingest command. The pipeline is idempotent — existing books are skipped, new ones are added:

```bash
cp new-cookbook.pdf ./incoming/
docker compose exec cookshelf python -m cooksLibrary.ingest
```

### Re-ingesting a Single Book

To re-process one book (e.g., after tuning the parser):

```bash
docker compose exec cookshelf python -m cooksLibrary.ingest --book <book-slug>
```

### Forcing Re-extraction

To ignore the text cache and re-extract all pages:

```bash
docker compose exec cookshelf python -m cooksLibrary.ingest --force
```

## Configuration

All configuration is via environment variables in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `COOKS_LIBRARY_PATH` | `/library/existing:/library/incoming` | Colon-separated list of directories to scan for PDFs |
| `COOKS_DB_PATH` | `/data/cooks.db` | SQLite database path |
| `COOKS_DATA_DIR` | `/data` | Data directory (page images, text cache) |
| `COOKS_CONFIDENCE_THRESHOLD` | `0.6` | Recipes below this confidence score fall back to PDF page rendering |
| `COOKS_CATEGORIES_FILE` | `/data/categories.yml` | Category rules file (editable, hot-reloaded by ingest) |
| `COOKS_LLM_MODEL` | _(unset)_ | LLM model for cleanup pass (optional) |
| `COOKS_LLM_API_KEY` | _(unset)_ | LLM API key for cleanup pass (optional) |

### Custom Categories

Edit `categories.yml` to control how books are categorized. The categorizer scores each book against keyword lists weighted by signal source (metadata, early pages, filename, folder):

```yaml
categories:
  - name: Instant Pot & Pressure Cooking
    keywords: [instant pot, pressure cooker, electric pressure]
    weight: 10
  - name: Desserts & Baking
    keywords: [dessert, cake, cookie, baking, pastry, pie, tart]
    weight: 5
  # Add your own...
```

### LLM Cleanup Pass (Optional)

For recipes that couldn't be fully parsed (low confidence score), an optional LLM cleanup pass can re-parse them using an LLM API:

```bash
docker compose exec cookshelf python -m cooksLibrary.ingest --llm-cleanup
```

Requires `COOKS_LLM_MODEL` and `COOKS_LLM_API_KEY` environment variables to be set.

## How It Works

### Ingest Pipeline

1. **Discovery** — walks library paths for PDFs, computes SHA-256 hashes for dedup
2. **Categorization** — scores books against keyword rules to assign categories
3. **Recipe Detection** — uses PDF outline (bookmarks) when available, or page-walk heuristics (SERVES markers, ingredient blocks) as fallback
4. **Text Sectioning** — splits recipe text into description, ingredients (grouped by section header), instructions, and servings
5. **Ingredient Parsing** — regex-based parser extracts quantity, unit, ingredient name, and notes
6. **Confidence Scoring** — weighted score (0.0-1.0) based on title, servings, ingredient count, instructions length, and unit ratio
7. **Indexing** — rebuilds FTS5 full-text index and ingredient index

Recipes scoring below the confidence threshold are marked `needs_review` and rendered as the original PDF page image instead of structured text.

### Web App

- Single FastAPI process serving pages, API, and static assets
- Server-rendered Jinja2 templates with HTMX for partial swaps (bookmark toggle, made toggle)
- Bootstrap 5 via CDN for responsive, mobile-friendly layouts
- SQLite as the sole data store — no separate database server
- Page images rendered lazily as WebP on first request, cached forever

## Development

### Running Tests

```bash
pip install -e .
python3 -m pytest -v
```

Tests that require real PDFs are skipped if the PDFs aren't available. To run those tests, set the path in the test files to point at a real cookbook PDF.

### Project Structure

```
src/cooksLibrary/
  config.py          # Environment variable loading
  db.py              # SQLite connection and migration
  schema.sql         # Database schema
  ingest/            # PDF ingestion pipeline
    cli.py           # CLI entry point
    detect.py        # Recipe detection (outline + page-walk)
    ingredients.py   # Ingredient line parser
    section.py       # Recipe text sectioning
    confidence.py    # Confidence scoring
    images.py        # Lazy page image rendering
    ...
  web/               # FastAPI web app
    main.py          # App factory
    queries.py       # Database access layer
    routes/          # Route handlers
    templates/       # Jinja2 templates
```

## License

Copyright (C) 2026 Jason Rennie

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for more details.