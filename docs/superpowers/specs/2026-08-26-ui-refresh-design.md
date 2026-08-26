# Cook's Library — UI Refresh Design Spec

**Date:** 2026-08-26
**Status:** Approved (pending user spec review)
**Depends on:** Cook's Library v1 (merged to master, commit d40fa2f)

A mobile-friendly UI refresh using Bootstrap 5, with "Made" recipe tracking and improved layout for browsing, bookmarking, and cooking.

---

## 1. Goals & Non-Goals

### Goals

- Replace Tailwind CSS with Bootstrap 5 (via CDN, no build step).
- Make all pages mobile-friendly with responsive layouts.
- Add a "Made" feature: mark recipes as made with a date stamp, browse a Made list sorted by recency.
- Use card-based layouts for browse/search/saved/made pages.
- Stacked single-column recipe detail page with checkable ingredient boxes.
- Filter chips on Saved and Made pages (All, By Category, By Book, Recent).
- Bootstrap hamburger navbar on mobile, inline links on desktop.

### Non-Goals

- User accounts or multi-user support (still single-user).
- Persisting ingredient checkbox state across page reloads (pure client-side).
- Ratings, notes, or reviews on made recipes (just toggle + date).
- Changing the ingest pipeline or data extraction logic.
- Server-side rendering of Bootstrap JS components (CDN only).

---

## 2. CSS Framework

**Swap Tailwind for Bootstrap 5 via CDN.** The current Tailwind setup requires downloading a standalone binary and a build step in the Dockerfile. Bootstrap via CDN is two `<link>`/`<script>` tags — no build pipeline, no binary, simpler Dockerfile.

**base.html head:**
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3/dist/js/bootstrap.bundle.min.js" defer></script>
<script src="https://unpkg.com/htmx.org@1.9" defer></script>
```

Bootstrap JS bundle includes: hamburger collapse, dropdowns (for filter chips), and modals. All from CDN, no build step.

**Custom CSS:** minimal — a small `<style>` block in `base.html` for recipe-specific tweaks (ingredient checkbox spacing, card image sizing). No separate CSS file to build or serve.

---

## 3. Data Model

New `made_recipes` table, added to `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS made_recipes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id   INTEGER NOT NULL UNIQUE REFERENCES recipes(id),
    made_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- Same toggle pattern as `bookmarks` — one row per recipe, `UNIQUE(recipe_id)`.
- Toggling "Made" inserts a row (with current timestamp) or deletes it.
- `made_at` stores when the recipe was marked as made.
- The Made list sorts by `made_at DESC` (most recent first).
- A recipe can be bookmarked without being made, and made without being bookmarked — they are independent flags. A recipe that is both will have rows in both tables.

**Migration:** `CREATE TABLE IF NOT EXISTS` means existing DBs get the new table on next `migrate()` call without touching existing data. No re-ingest needed.

**New query functions** (in `queries.py`):
- `toggle_made(recipe_id) -> bool` — insert or delete, return new state
- `is_made(recipe_id) -> bool` — check if row exists
- `get_made_recipes() -> list[dict]` — join `made_recipes` + `recipes` + `books`, ordered by `made_at DESC`

Existing `bookmarks` table and queries are unchanged.

---

## 4. Layout

### Navbar (Bootstrap navbar with hamburger collapse)

- Sticky top navbar, Bootstrap `navbar-expand-lg` — hamburger on mobile, inline links on desktop.
- Nav items: Home, Books, Search, Saved, Made.
- Brand "Cook's Library" on the left.

### Card grid (browse/search/saved/made)

Bootstrap responsive grid:
- Phone: 1 column (`col-12`)
- Tablet: 2 columns (`col-sm-6`)
- Desktop: 3 columns (`col-md-4`)
- Large: 4 columns (`col-lg-3`)

Each card shows: recipe title, book title, servings, bookmark icon, made icon. Clicking the card opens the recipe detail page.

### Recipe detail (stacked single column)

- Container: `col-md-8 col-lg-6 mx-auto` (centered, constrained width on desktop for readability).
- Header: title, book title, page, servings. Bookmark and Made buttons inline.
- Description paragraph (if present).
- Ingredients section with checkable checkboxes (`<input type="checkbox">` with Bootstrap `form-check` styling). Grouped by section header (FOR THE CRUST, etc.) when present.
- Instructions section below ingredients.
- "View original PDF page" link at the bottom.
- Ingredient checkbox state is purely client-side — resets on page reload.

### Saved & Made pages (separate pages with filter chips)

- Filter chips: a row of Bootstrap pill buttons at the top.
  - "All" (default)
  - "By Category" (dropdown of categories)
  - "By Book" (dropdown of books)
  - "Recent" (sorts by `created_at`/`made_at` DESC)
- Filters use HTMX — clicking a chip swaps the card grid below without a full page reload.
- Card grid below the filters, same `recipe_card.html` partial.
> **Note:** Filter chips are deferred to a follow-up iteration. The pages currently render the full list sorted by date — the filtering can be added without restructuring the templates.

---

## 5. Routes

| Method | Path | Purpose | Changes |
|--------|------|---------|---------|
| GET | `/` | Home | Bootstrap card grid |
| GET | `/books` | Book list | Bootstrap card grid |
| GET | `/books/{slug}` | Book detail | Bootstrap list-group |
| GET | `/books/{slug}/page/{n}` | Page image | Unchanged |
| GET | `/recipes/{id}` | Recipe detail | Stacked layout, checkboxes, Made button |
| GET | `/search?q=…&type=…` | Search | Card grid results |
| GET | `/ingredients` | Ingredient list | Bootstrap styling |
| GET | `/ingredients/{name}` | Ingredient detail | Bootstrap styling |
| POST | `/bookmarks` | Toggle bookmark | Unchanged logic, Bootstrap-styled partial |
| DELETE | `/bookmarks/{recipe_id}` | Remove bookmark | Unchanged |
| GET | `/bookmarks` | Saved list | **Modified** — filter chips + card grid |
| GET | `/made` | Made list | **New** — filter chips + card grid |
| POST | `/made` | Toggle made | **New** — HTMX, returns partial |
| DELETE | `/made/{recipe_id}` | Remove from made | **New** |
| GET | `/health` | Liveness | Unchanged |

---

## 6. Templates

| Template | Status | Changes |
|----------|--------|---------|
| `base.html` | Modified | Bootstrap 5 CDN, hamburger navbar, remove Tailwind link |
| `home.html` | Modified | Bootstrap card grid |
| `book_list.html` | Modified | Bootstrap card grid |
| `book_detail.html` | Modified | Bootstrap list-group |
| `recipe.html` | Modified | Stacked layout, ingredient checkboxes, Made button |
| `recipe_fallback.html` | Modified | Bootstrap image styling, Made button |
| `search_results.html` | Modified | Card grid using `recipe_card.html` partial |
| `bookmarks.html` | Modified | Filter chips + card grid |
| `ingredient_list.html` | Modified | Bootstrap styling |
| `ingredient_detail.html` | Modified | Bootstrap styling |
| `partials/bookmark_button.html` | Modified | Bootstrap-styled |
| `partials/made_button.html` | New | HTMX toggle, "✓ Made" (green) or "Mark as Made" |
| `partials/recipe_card.html` | New | Shared card for browse/search/saved/made grids |
| `made.html` | New | Same layout as bookmarks.html, for made recipes |

---

## 7. Docker Changes

**Dockerfile simplification:**
- Remove: `curl` download of Tailwind binary, `tailwindcss` build step
- Remove: `src/cooksLibrary/web/static/css/input.css`, `app.css`
- Keep: `poppler-utils`, `webp`, `pip install`, `PYTHONPATH`, `uvicorn` CMD
- No changes to `docker-compose.yml` (ports, mounts, env vars unchanged)

**Rebuild:**
1. `docker compose build` — picks up simplified Dockerfile
2. `docker compose up -d` — restart with new templates
3. No re-ingest needed — data unchanged, only presentation layer

---

## 8. Testing

- Update existing web tests to reflect Bootstrap HTML structure (class names, layout elements).
- New tests for `toggle_made`, `is_made`, `get_made_recipes` query functions.
- New tests for `GET /made`, `POST /made`, `DELETE /made/{id}` routes.
- New test for `made_button.html` partial (HTMX swap returns correct state).
- Existing ingest, detection, and parsing tests are unchanged.

---

## 9. Scope Notes

- The 1,471 `pdf_fallback` recipes will still show page images — the stacked layout applies the same Bootstrap styling to the fallback template.
- The `Uncategorized` books (18) and ISBN-filename titles are a pre-existing data quality issue, not addressed by this UI refresh.
- FTS5 query sanitization and search modes (`type=ingredient`, `type=category`) remain deferred from v1.