# Cook's Library — Design Spec

**Date:** 2026-08-25
**Status:** Approved (pending user spec review)
**Author:** brainstormed with user

A self-hosted, LAN-accessible web app for browsing, searching, and bookmarking recipes extracted from a personal collection of cookbook PDFs.

---

## 1. Goals & Non-Goals

### Goals (v1)

- Ingest ~62 cookbook PDFs (~3.4 GB) located under `/mnt/media/Komga/Cooking` and extract recipes into a searchable store.
- Browse the library by book and by content-derived category.
- Full-text search across recipes plus ingredient-based search.
- View a recipe as clean structured text (title, description, ingredients, instructions, servings) with a link to the original PDF page image.
- Per-recipe PDF fallback view when extraction confidence is low.
- Bookmark recipes; view all bookmarks.
- Add new PDFs at runtime by dropping them into a writable incoming directory; no code changes or location dependency.
- Categorize books by content (metadata + early-page text + filename), not by source folder.
- Single container, SQLite database, runs on a home server, accessible from any LAN device.

### Non-Goals (v1)

- User accounts and authentication. Single-user assumption.
- Meal planning and shopping-list generation. (Future v2.)
- OCR for uploaded camera images. (Future v2.)
- Cloud deployment or internet exposure.
- Editing extracted recipes in the UI. (Manual category override is reserved in the schema for v2 but not exposed in v1.)
- A SPA frontend or any Node toolchain.

### Future Work (explicitly deferred)

- **OCR uploads:** accept camera/web images, run OCR, store as a "book" with an image source. Same `recipes` schema supports it; only the ingest front-end changes.
- **Meal planning & shopping lists:** pick recipes for a week, combine ingredient quantities, de-duplicate. Requires a normalized ingredient-name layer, which `ingredient_index` already anticipates.
- **Admin UI for category overrides** and ingredient alias management.
- **LLM-assisted extraction** as a cleanup pass is in v1 scope (below), but it is optional and off by default.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Source PDFs (read-only)            Incoming PDFs (writable)        │
│  /library/existing/**.pdf          /library/incoming/**.pdf        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                   ┌───────────▼───────────┐
                   │  Ingest pipeline      │  one-shot, re-runnable
                   │  (Python CLI)         │  idempotent: re-running
                   │                       │  updates, never duplicates
                   │  1. Discover books    │
                   │  2. Derive category   │
                   │  3. Extract recipes   │
                   │     (outline or       │
                   │      page-walk)       │
                   │  4. Parse ingredients │
                   │     (heuristic)       │
                   │  5. Score confidence  │
                   │  6. Index (FTS5 +     │
                   │     ingredient_index)│
                   │  7. Write SQLite      │
                   │                       │
                   │  (page images rendered│
                   │   lazily at read time │
                   │   by the web app)    │
                   └───────────┬───────────┘
                               │
              ┌────────────────▼─────────────────┐
              │  SQLite (cooks.db)                │
              │  - books, recipes, ingredients    │
              │  - bookmarks                      │
              │  - FTS5 full-text index           │
              └────────────────┬─────────────────┘
                               │
              ┌────────────────▼─────────────────┐
              │  Web app (FastAPI + Jinja/HTMX)   │  single container
              │  - Browse books/recipes           │  served on 0.0.0.0
              │  - Full-text + ingredient search  │  port 8000
              │  - Recipe view (text + page img)  │
              │  - Bookmarks                      │
              │  - Static assets / page images    │
              └───────────────────────────────────┘
                               │
                  LAN access from any device
```

### Key properties

- **One container, one process group.** FastAPI serves API, pages, and static assets. SQLite is a file. No separate DB server.
- **Ingest is decoupled from serving.** The CLI writes to the same SQLite file the app reads. Re-running ingest after adding PDFs does not require stopping the app (SQLite handles concurrent reads; writes are wrapped in a transaction).
- **Source PDFs stay read-only.** The app never mutates them. Rendered page images and extracted text live in a `data/` directory.
- **LLM cleanup pass is a separate CLI flag** (`ingest --llm-cleanup`) that only touches low-confidence recipes. Default ingest is heuristic-only and fully offline.

---

## 3. Data Model

### `books`

| column              | type      | notes                                                      |
|---------------------|-----------|------------------------------------------------------------|
| id                  | INTEGER PK|                                                            |
| slug                | TEXT UNIQUE | `"eat-like-a-man-guide-to-feeding-a-crowd"`              |
| title               | TEXT      | from PDF metadata or prettified filename                   |
| author              | TEXT      | from PDF metadata, nullable                                |
| category            | TEXT      | content-derived (see §5), `"Uncategorized"` if none match  |
| category_override   | TEXT      | nullable, reserved for v2 admin UI                         |
| source_path         | TEXT      | absolute path inside container                             |
| source_hash         | TEXT UNIQUE | content hash (SHA-256 of file bytes), for dedup across library paths |
| page_count          | INTEGER   |                                                            |
| pdf_version         | TEXT      |                                                            |
| ingested_at         | TIMESTAMP |                                                            |
| ingest_method       | TEXT      | `"outline"`, `"page-walk"`, or `"hybrid"`                  |
| outline_present     | BOOLEAN   |                                                            |

### `recipes`

| column              | type      | notes                                                      |
|---------------------|-----------|------------------------------------------------------------|
| id                  | INTEGER PK|                                                            |
| book_id             | INTEGER FK → books |                                                |
| title               | TEXT      |                                                            |
| page_start          | INTEGER   | 1-indexed PDF page                                         |
| page_end            | INTEGER   | nullable; spans multiple pages                             |
| description         | TEXT      | headnote paragraph(s), nullable                            |
| servings            | TEXT      | original string, e.g. `"4 to 6"`                           |
| servings_min        | INTEGER   | parsed lower bound                                         |
| servings_max        | INTEGER   | parsed upper bound (== min if single value)               |
| instructions        | TEXT      | extracted instruction text                                 |
| confidence          | REAL      | 0.0–1.0, set by parser (see §6.4)                          |
| needs_review        | BOOLEAN   | `confidence < threshold`                                   |
| render_method       | TEXT      | `"structured"` or `"pdf_fallback"`                         |
| extraction_notes    | TEXT      | debug info: why confidence is low                          |
| UNIQUE(book_id, page_start) |     |                                                            |

### `recipe_ingredients`

| column              | type      | notes                                                      |
|---------------------|-----------|------------------------------------------------------------|
| id                  | INTEGER PK|                                                            |
| recipe_id           | INTEGER FK → recipes |                                                |
| position            | INTEGER   | display order                                              |
| section             | TEXT      | `"FOR THE CRUST"`, `""` when none                          |
| quantity            | TEXT      | `"2"`, `"1 ¼"`, `"1/2"`                                    |
| quantity_norm        | REAL      | numeric form, nullable                                     |
| unit                | TEXT      | `"cups"`, `"oz"`, `"tsp"`, `""`                            |
| ingredient_name     | TEXT      | `"all-purpose flour"`                                       |
| note                | TEXT      | `"minced"`, `"at room temperature"`                        |
| raw_text            | TEXT      | verbatim line, e.g. `"1 ¼ cups/300 ml buttermilk"`          |
| UNIQUE(recipe_id, position) |     |                                                            |

### `ingredient_index`

| column              | type      | notes                                                      |
|---------------------|-----------|------------------------------------------------------------|
| ingredient_name     | TEXT PK   | normalized lowercase, e.g. `"all-purpose flour"`            |
| display_name        | TEXT      | `"All-Purpose Flour"`                                      |
| recipe_count        | INTEGER   | denormalized for fast browse                               |
| aliases             | JSON      | `["flour", "ap flour"]`, populated manually later          |

### `bookmarks`

| column              | type      | notes                                                      |
|---------------------|-----------|------------------------------------------------------------|
| id                  | INTEGER PK|                                                            |
| recipe_id           | INTEGER FK → recipes | UNIQUE — one bookmark per recipe                |
| created_at          | TIMESTAMP |                                                            |
| note                | TEXT      | free text, nullable                                        |

### Full-text index

A SQLite FTS5 virtual table `recipes_fts` mirrors `(title, description, instructions, ingredient_names)` from `recipes`, kept in sync via triggers. Querying joins back to `recipes` for display. `ingredient_names` is a space-joined string of all `recipe_ingredients.ingredient_name` values for the recipe.

### Storage layout on disk

```
data/
  cooks.db
  page_images/
    {book_slug}/{page:04d}.webp        rendered PDF pages, lazily rendered
  text_cache/
    {book_slug}/{page:04d}.txt        raw pdftotext output, cached
  categories.yml                       editable category rules (mounted)
```

### Design choices worth flagging

1. **One row per ingredient line, not per ingredient.** `ingredient_index` is the searchable normalized index built from `recipe_ingredients.ingredient_name`. This separates "what's on the page" from "what's searchable" and lets aliases merge names later without touching recipe rows.
2. **`needs_review` + `confidence` rather than pass/fail.** The UI highlights low-confidence recipes, and the LLM cleanup pass targets rows where `needs_review = true`. Threshold is configurable (default 0.6).
3. **`render_method` per recipe, not per book.** Even a well-parsed book may have one weird recipe; the fallback decision is local.

---

## 4. Configuration

Environment variables (read once at app startup, passed through to ingest CLI):

| variable                      | default                              | notes                                  |
|-------------------------------|--------------------------------------|----------------------------------------|
| `COOKS_LIBRARY_PATH`          | `/library/existing:/library/incoming` | colon-separated, walked in order       |
| `COOKS_DB_PATH`               | `/data/cooks.db`                     |                                        |
| `COOKS_DATA_DIR`              | `/data`                              |                                        |
| `COOKS_CONFIDENCE_THRESHOLD`  | `0.6`                                | `--threshold` flag on ingest CLI       |
| `COOKS_CATEGORIES_FILE`       | `/data/categories.yml`               | editable, hot-reloaded by ingest       |
| `COOKS_LLM_MODEL`             | `glm-5.2`                            | only used by `--llm-cleanup`           |
| `COOKS_LLM_API_KEY`           | _(unset)_                            | only used by `--llm-cleanup`           |

---

## 5. Categorization

Books are categorized by content, not source folder. A small rule-based classifier runs at ingest.

### `categories.yml`

```yaml
categories:
  Instant Pot & Pressure Cooking:
    keywords: [instant pot, pressure cooker, electric pressure]
    weight: 10
  Desserts & Baking:
    keywords: [dessert, cake, cookie, baking, pastry, pie, tart, sweet, cheesecake, brownie]
    weight: 5
  Cocktails & Drinks:
    keywords: [cocktail, martini, drink, spirits, bourbon, whiskey, margarita, mocktail]
    weight: 10
  Vegetables & Vegetarian:
    keywords: [vegetable, vegetarian, vegan, "fresh & green", produce]
    weight: 5
  Pasta & Italian:
    keywords: [pasta, italian, risotto, lasagna, bolognese]
    weight: 5
  # user can add more
```

### Scoring per book

```
signals (in priority order):
  1. PDF metadata Title + Keywords  (×3 weight)
  2. First 5 pages of text          (×2 weight)  — TOC + intro usually here
  3. Filename                       (×1 weight)
  4. Parent folder name             (×1 weight, last-resort fallback)

for each category:
  score = sum(keyword_hits × keyword_weight) × signal_weight
category = argmax(score)
if max(score) < threshold: category = "Uncategorized"
```

Stored as `books.category`. The folder name is just one signal — a book filed under "Weekend Cooking" that's clearly about cocktails will get `Cocktails & Drinks`. If `books.category_override` is set (v2), it takes precedence over the derived value.

---

## 6. Ingest Pipeline

Single CLI: `python -m cooksLibrary.ingest`. Idempotent — re-running updates rows by matching `(books.source_hash)` and `(recipes.book_id, recipes.page_start)`, never duplicates.

### 6.1 Stage 1 — Book discovery & metadata

```
walk COOKS_LIBRARY_PATH entries for *.pdf
  ↓
for each PDF:
  sha256 of file bytes -> source_hash (dedup across library paths)
  pdfinfo -> page_count, pdf_version, metadata (Title/Author)
  title = metadata.Title or prettified filename
  collection = parent folder name (used only as one categorization signal)
  upsert into books (match on source_hash)
```

~62 PDFs, a few seconds.

### 6.2 Stage 2 — Recipe detection (two paths, picked per book)

**Path A: outline-driven** (when `books.outline_present = true` and outline has ≥ 5 leaf entries):

```
read PDF outline with pypdf
flatten to (title, page_number) pairs
filter: drop entries matching a stoplist regex
  (Cover, Title, Copyright, Contents, Introduction, Index,
   Acknowledgments, Credits, "How to …" sidebars)
remaining entries are recipe candidates
```

Each candidate becomes a recipe row with `page_start = page_number`. `page_end` is the next recipe's `page_start − 1` (or book end).

**Path B: page-walk** (no usable outline):

```
for each page 1..N:
  pdftotext -layout page -> text (cached in data/text_cache/)
  detect recipe start via signals:
    S1  largest font line on page is short (< 60 chars)    [needs pdfplumber for font size]
    S2  page contains "SERVES" / "Serves N" / "MAKES N"    [strong]
    S3  page contains an ingredients block (>=4 lines matching
        the ingredient-line regex within a column region)
    S4  previous page ended a recipe (contained instructions + servings)
  if S2 AND (S1 OR S3): mark as recipe start
group consecutive pages into a recipe (page_start .. page_end)
```

Page-walk is slower (~1–2 s per page with pdfplumber). Books with outlines skip it.

**Hybrid** (default for books with shallow outlines — e.g. a single "Recipes" entry at p.12): run page-walk *within the outline's page ranges only*. Recorded as `ingest_method = "hybrid"`.

### 6.3 Stage 3 — Recipe text extraction & sectioning

For each detected recipe, extract text for pages `page_start..page_end` and split into:

- **title** — first non-empty line, biggest font, or outline title
- **description** — paragraph(s) between title and first ingredient/instruction marker
- **ingredients** — lines matching the ingredient-line regex, grouped by `"FOR THE …"` / `"CRUST:"` / `"FILLING:"` headers
- **instructions** — remaining narrative/numbered text after ingredients
- **servings** — regex match for `Serves N` / `SERVES N` / `MAKES N`

**Ingredient-line regex** (the workhorse — handles all observed formats):

```
^(?P<qty>\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?|\d+\s+\d+/\d+)\s*
(?P<unit>cup|cups|tbsp|tablespoons?|tsp|teaspoons?|oz|ounces?|
          lb|lbs|pounds?|g|kg|ml|l|liters?|cans?|packages?|
          cloves?|sticks?|sprigs?|bunches?|pinches?)?\s*
(?P<name>.*?)(?:,\s*(?P<note>.*))?$
```

A secondary pattern strips `/480 ml` dual-unit suffixes into the `raw_text` only (dropped from normalized fields). Lines that do not match get stored with `quantity = NULL` and `needs_review = true`.

### 6.4 Stage 4 — Confidence scoring

Each recipe gets `confidence ∈ [0.0, 1.0]` from a weighted sum:

| signal                                                   | weight |
|----------------------------------------------------------|--------|
| has title (non-empty, < 80 chars)                        | 0.30   |
| has servings parsed                                      | 0.20   |
| has ≥ 3 ingredient lines that matched the regex          | 0.20   |
| has ≥ 50 chars of instructions                           | 0.15   |
| ingredient lines mostly use units from the known list    | 0.10   |
| page-walk signal strength (Path B only)                  | 0.05   |

`needs_review = (confidence < threshold)`, default threshold 0.6, configurable via `--threshold`. Recipes with `needs_review = true` get `render_method = "pdf_fallback"` automatically; the UI shows the rendered page and no structured ingredient list.

### 6.5 Stage 5 — Page image rendering (lazy)

```
on demand at read time (first GET /books/{slug}/page/{n}):
  pdftoppm -png -r 150 -f N -l N book.pdf /tmp/page
  cwebp -> data/page_images/{slug}/{N:04d}.webp
  cached forever
```

Lazy rendering, not at ingest time. 62 books × ~50 recipes × ~150 KB ≈ ~500 MB if everything is viewed, but most recipes never get viewed. Served as static files with long cache headers.

### 6.6 Stage 6 — Indexing

After all recipes are inserted/updated:

```
rebuild recipes_fts (FTS5) from recipes + joined ingredient_names
update ingredient_index:
  for each distinct ingredient_name across all recipes:
    normalize to lowercase, title-case display name
    count recipes
    (aliases populated manually later via admin route in v2)
```

### 6.7 Stage 7 — LLM cleanup pass (optional, separate command)

```
python -m cooksLibrary.ingest --llm-cleanup
  ↓
select recipes where needs_review = true
  ↓
for each:
  build prompt from cached page text + the heuristic parse attempt
  call COOKS_LLM_MODEL with strict JSON schema response:
    {title, servings, ingredients[{quantity, unit, name, note}], instructions}
  ↓
  validate JSON, re-score confidence (LLM output gets 0.9 baseline)
  ↓
  if validation passes: update row, clear needs_review, render_method = "structured"
  else: leave as pdf_fallback
```

Cost-controlled: `--max-recipes N` flag (default 0 = all), `--dry-run` to preview which recipes would be sent. Every change is logged so it can be audited.

### 6.8 Re-runnability

- `--book <slug>` re-ingests one book (useful while tuning the parser)
- `--force` ignores the `ingested_at` cache and re-extracts text
- `--threshold 0.7` raises/lowers the bar
- Text extraction is cached in `data/text_cache/`, so iterating on the parser does not re-pay PDF extraction cost

---

## 7. Web App

Single FastAPI process serving API + pages + static assets. Server-rendered Jinja2 + HTMX for interactivity (no SPA, no Node build pipeline).

### 7.1 Routes

| method | path                            | purpose                                            |
|--------|---------------------------------|----------------------------------------------------|
| GET    | `/`                             | Home: search bar, recent bookmarks, category browse |
| GET    | `/books`                        | All books, grouped by category                      |
| GET    | `/books/{slug}`                 | Book detail: cover, metadata, recipe list           |
| GET    | `/books/{slug}/page/{n}`        | Raw PDF page image (cached, lazy-rendered)          |
| GET    | `/recipes/{id}`                 | Recipe view (the main screen)                       |
| GET    | `/search?q=…&type=…`            | Search: full-text / ingredient / category           |
| GET    | `/ingredients`                  | A–Z ingredient browser with recipe counts           |
| GET    | `/ingredients/{name}`           | Recipes containing this ingredient                  |
| POST   | `/bookmarks`                    | Toggle bookmark on a recipe (HTMX)                  |
| DELETE | `/bookmarks/{recipe_id}`        | Remove bookmark                                    |
| GET    | `/bookmarks`                    | All bookmarked recipes                              |
| GET    | `/health`                       | Liveness (for docker)                              |
| GET    | `/api/…`                        | JSON variants of the above for future scripting     |

### 7.2 Recipe view (`GET /recipes/{id}`)

Layout:

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back   Salted Caramel Cheesecake with Pretzel Crumb Crust │
│                                            [♥ Bookmark]      │
│  from Williams Sonoma Test Kitchen: The Instant Pot         │
│  Desserts Cookbook · p.12  · Serves 8                       │
├─────────────────────────────────────────────────────────────┤
│  Use your favorite salted caramel sauce—homemade or         │
│  store-bought—for this easy cheesecake…                     │
├─────────────────────────────┬───────────────────────────────┤
│  FOR THE CRUST              │   To make the crust, lightly   │
│  • 1 cup fine pretzel       │   spray a 7-inch springform    │
│     crumbs (about 4 oz)     │   pan with nonstick cooking    │
│  • 2 tbsp light brown       │   spray…                       │
│     sugar                   │                                │
│  • 4 tbsp unsalted butter,  │   To make the filling, in a    │
│     melted                 │   stand mixer fitted with…     │
│                             │                                │
│  FOR THE FILLING            │                                │
│  • 2 packages (8 oz each)   │                                │
│     cream cheese, at room   │                                │
│     temperature             │                                │
│  …                          │                                │
├─────────────────────────────┴───────────────────────────────┤
│  [View original PDF page]   ← opens /books/{slug}/page/12   │
└─────────────────────────────────────────────────────────────┘
```

- **Structured view** when `render_method = "structured"`: left column ingredients (grouped by section header), right column instructions. Bookmark button is an HTMX POST that swaps the button label in place.
- **PDF fallback view** when `render_method = "pdf_fallback"`: shows the rendered page image(s) for `page_start..page_end` instead of the structured columns. Same header (title, book, page), same bookmark button. No ingredient checklist on these.
- **"View original PDF page"** link appears on both views — opens the page image in a new tab.

### 7.3 Search (`GET /search?q=…&type=…`)

Three modes, same URL with `type` param:

- **`type=text` (default):** FTS5 query across `title + description + instructions + ingredient_names`. Results show title, book, snippet with the matched term highlighted (FTS5 `snippet()` function), page number.
- **`type=ingredient`:** exact match against `ingredient_index.ingredient_name` or any alias. Results are recipes containing that ingredient, ranked by relevance. A sidebar shows related ingredients.
- **`type=category`:** filter by `books.category`. Combined with a text query when `q` is present.

Results page uses HTMX infinite scroll (load more on scroll) to keep the first page fast.

### 7.4 Bookmarks

- One per recipe (`UNIQUE(recipe_id)`). No user accounts in v1 — single-user assumption for a personal library on the LAN.
- Bookmark button appears anywhere a recipe is shown (search results, recipe view, book detail). All hit `POST /bookmarks` with the recipe id; HTMX swaps the button.
- `/bookmarks` shows all bookmarked recipes in a grid, grouped by book, sortable by date added.

### 7.5 Frontend stack & aesthetics

- **Jinja2 templates** + **HTMX** + **Alpine.js** (tiny, only where state is needed, e.g. search-as-you-type dropdown).
- **Tailwind** via standalone CLI binary (no Node toolchain — single binary build step in Docker).
- Server-rendered by default, HTMX for partial swaps. No SPA, no React.
- Clean, readable, mobile-friendly. Two-column on desktop, stacked on phone. Larger type, generous spacing — designed for reading in the kitchen.

### 7.6 Static asset serving

- FastAPI `StaticFiles` mounts:
  - `/static/*` → app CSS/JS (built once at image build time)
  - `/page_images/*` → `data/page_images/` (rendered PDF pages)
- Page images served with long cache headers (`Cache-Control: max-age=31536000`) since they're immutable.

---

## 8. Deployment

### 8.1 Dockerfile

```
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
      poppler-utils libwebp-tools && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# tailwindcss standalone binary downloaded in build step
COPY app/ /app
RUN tailwind build
CMD ["uvicorn", "cooksLibrary.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 docker-compose.yml

```yaml
services:
  cooks-library:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - /mnt/media/Komga/Cooking:/library/existing:ro
      - ./incoming:/library/incoming
      - cooks-data:/data
    environment:
      COOKS_LIBRARY_PATH: /library/existing:/library/incoming
      COOKS_DB_PATH: /data/cooks.db
      COOKS_DATA_DIR: /data
      COOKS_CONFIDENCE_THRESHOLD: "0.6"
      COOKS_CATEGORIES_FILE: /data/categories.yml
      # COOKS_LLM_MODEL: glm-5.2        # only for --llm-cleanup
      # COOKS_LLM_API_KEY: ...          # only for --llm-cleanup
    restart: unless-stopped

volumes:
  cooks-data:
```

### 8.3 Container mount layout

- `/library/existing` — the existing collection, mounted read-only from the host's `/mnt/media/Komga/Cooking`.
- `/library/incoming` — writable; drop new PDFs here.
- `/data` — persisted volume holding `cooks.db`, `page_images/`, `text_cache/`, and `categories.yml`.

Adding a new PDF at runtime: drop it into `./incoming` on the host, run `docker compose exec cooks-library python -m cooksLibrary.ingest`, refresh the page.

---

## 9. Testing Strategy

- **Unit tests** for the ingredient-line regex against a corpus of real ingredient lines sampled from the PDFs (golden-file approach: real inputs, expected structured outputs). Guards the parser as it evolves.
- **Unit tests** for the categorizer with synthetic book metadata and expected categories.
- **Integration test** for the ingest pipeline against a small fixture PDF (a 5-page synthetic cookbook with 2 recipes), asserting the resulting DB rows.
- **Integration tests** for web routes using FastAPI's `TestClient`: search, recipe view, bookmark toggle, page image rendering.
- **Smoke test** script that runs ingest on one real book from the collection and asserts ≥ 1 recipe with `confidence >= threshold`.

No live LLM calls in tests — the cleanup pass is tested against a mocked LLM endpoint returning canned JSON.

---

## 10. Open Questions

None blocking. The following are deferred to implementation and do not require spec-level decisions:

- Exact set of stoplist regexes for outline filtering (tunable post-ingest).
- Final list of categories in `categories.yml` (user-editable, hot-reloadable).
- Default confidence threshold value (configurable, default 0.6).
- Whether to ship a Tailwind binary in the image or download it at build time.