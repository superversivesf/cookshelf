# Shopping List Feature Design Spec

**Date:** 2026-08-27
**Status:** Approved (pending user spec review)
**Depends on:** Cookshelf v1 + UI refresh (merged to master)

A server-side shopping list that pulls ingredient lines from a recipe, persists them, and lets you check items off as you shop.

---

## 1. Goals & Non-Goals

### Goals

- Add a recipe's ingredients to a persistent shopping list with one click from the recipe page.
- View the shopping list as checkable rows — tap to strike through, tap again to unstrike.
- Clear the list when done.
- One active list at a time — adding a new recipe's ingredients replaces the current list.
- Server-side persistence (SQLite) — survives browser reloads and device switching on the LAN.
- Mobile-friendly: large tap targets, sticky header, full-width rows.

### Non-Goals

- Multiple named lists (deferred — one list replaces each time).
- Combining multiple recipes into one list (deferred — single recipe at a time).
- Ingredient normalization or deduplication (the list shows raw_text verbatim from the recipe page).
- Quantities scaling by serving size.
- Printing or exporting the list (can use the browser's print function).
- Changes to the existing client-side ingredient checkboxes on the recipe page.

---

## 2. Data Model

New `shopping_list` table, added to `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS shopping_list (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id       INTEGER NOT NULL,
    recipe_title    TEXT NOT NULL,
    ingredient_text TEXT NOT NULL,
    checked         INTEGER NOT NULL DEFAULT 0,
    added_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- No foreign key on `recipe_id` — the list survives re-ingestion even if recipe IDs change. `recipe_title` is a denormalized copy for display.
- `ingredient_text` stores the `raw_text` line from `recipe_ingredients` — the verbatim ingredient line as it appears on the recipe page.
- `checked` is 0 (unchecked) or 1 (checked off / strikethrough).
- `added_at` tracks when the item was added (for ordering).

Migration uses `CREATE TABLE IF NOT EXISTS` — existing DBs get the table on next `migrate()` call.

---

## 3. Query Functions

New functions in `src/cooksLibrary/web/queries.py`:

- `add_recipe_to_shopping_list(recipe_id: int) -> dict` — clears existing list, inserts all `recipe_ingredients.raw_text` rows for the recipe (ordered by position), returns `{"recipe_title": str, "item_count": int}`.
- `get_shopping_list() -> list[dict]` — returns all rows ordered by `added_at`, with `checked` state. Each row: `id`, `recipe_id`, `recipe_title`, `ingredient_text`, `checked`.
- `toggle_shopping_list_item(item_id: int) -> bool` — flip `checked` 0↔1, return new state.
- `clear_shopping_list() -> None` — delete all rows.

---

## 4. Routes

New router in `src/cooksLibrary/web/routes/shopping.py`:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/shopping` | Shopping list page (full HTML) |
| POST | `/shopping/add/{recipe_id}` | Add recipe's ingredients (HTMX — returns shopping list partial or redirect) |
| POST | `/shopping/toggle/{item_id}` | Toggle check-off (HTMX — returns updated row partial) |
| POST | `/shopping/clear` | Clear the list (HTMX — returns empty state partial) |

Include in `main.py` alongside existing routers.

---

## 5. Templates

| Template | Status | Purpose |
|----------|--------|---------|
| `shopping.html` | New | Shopping list page: header with recipe title + Clear button, list of checkable ingredient rows, empty state, "View recipe" link |
| `partials/shopping_list_row.html` | New | Single ingredient row with checkbox — used for HTMX toggle swap |
| `partials/shopping_list_items.html` | New | Full list of rows — used for HTMX add/clear swap |
| `partials/shopping_list_button.html` | New | "Add to Shopping List" button on the recipe page |
| `base.html` | Modified | Add "Shopping" nav item after "Made" |
| `recipe.html` | Modified | Include shopping_list_button partial in the button row |
| `recipe_fallback.html` | Modified | Include shopping_list_button partial in the button row |

### Shopping list page layout

```
┌─────────────────────────────────────────────┐
│  Shopping List                    [Clear All] │
│                                               │
│  From: Mediterranean Strata                   │
│                                               │
│  □ 1 tbsp unsalted butter                     │
│  ☑ 1/4 lb crusty Italian bread, cubed        │
│  □ 1 can (14 oz) artichoke hearts             │
│  ...                                          │
│                                               │
│  [View recipe]                                │
└─────────────────────────────────────────────┘
```

- Ingredient rows: Bootstrap `form-check` with checkbox + label. Checked items get `text-decoration-line-through text-muted`.
- Tapping a checkbox fires `POST /shopping/toggle/{item_id}` via HTMX, swaps the row in place.
- "Clear All" fires `POST /shopping/clear`, swaps the list area with the empty state.
- "View recipe" links to `/recipes/{recipe_id}`.
- Empty state: "Your shopping list is empty. Add ingredients from any recipe."
- Container: `col-12 col-md-8 col-lg-6 mx-auto` (centered, constrained width for readability).

### Recipe page button

The "Add to Shopping List" button sits in the button row alongside Save and Made:
- Unadded state: `btn btn-outline-primary btn-sm` — text "Add to List"
- After adding: swaps to `btn btn-success btn-sm` — text "On List" with link to `/shopping`
- HTMX POST to `/shopping/add/{recipe_id}`, swaps the button in place.

---

## 6. Navbar

Add "Shopping" nav item after "Made" in the Bootstrap navbar:
```html
<li class="nav-item"><a class="nav-link" href="/shopping">Shopping</a></li>
```

---

## 7. Testing

- New `tests/test_web_shopping.py`:
  - `test_add_recipe_to_shopping_list` — POST adds ingredients, GET shows them
  - `test_toggle_item` — POST toggle flips checked state
  - `test_clear_list` — POST clear empties the list
  - `test_shopping_page_empty` — GET /shopping with no items shows empty state
  - `test_shopping_page_shows_items` — GET /shopping with items shows them
- Update existing recipe tests to verify the "Add to List" button is present.
- All existing tests must continue to pass.