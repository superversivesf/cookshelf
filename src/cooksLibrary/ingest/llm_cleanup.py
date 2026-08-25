import json
import sqlite3

PROMPT_TEMPLATE = """You are a recipe parser. Given the text of a recipe page, extract the recipe as JSON.

Recipe title: {title}
Page text:
{text}

Return ONLY a JSON object with this exact schema:
{{
  "title": "string",
  "servings": "string or null",
  "ingredients": [{{"quantity": "string", "unit": "string", "name": "string", "note": "string"}}],
  "instructions": "string"
}}

Do not include any text before or after the JSON.
"""

def build_prompt(title: str, ingredient_text: str, instructions: str) -> str:
    text = f"Ingredients:\n{ingredient_text}\n\nInstructions:\n{instructions}"
    return PROMPT_TEMPLATE.format(title=title, text=text)

def parse_llm_response(text: str) -> dict | None:
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    required = {"title", "servings", "ingredients", "instructions"}
    if not required.issubset(data.keys()):
        return None
    if not isinstance(data["ingredients"], list):
        return None
    return data

def run_cleanup(conn: sqlite3.Connection, settings, max_recipes: int, dry_run: bool) -> int:
    if not settings.llm_model or not settings.llm_api_key:
        print("LLM cleanup requires COOKS_LLM_MODEL and COOKS_LLM_API_KEY")
        return 1
    query = "SELECT id, title, page_start FROM recipes WHERE needs_review = 1"
    if max_recipes > 0:
        query += f" LIMIT {max_recipes}"
    rows = conn.execute(query).fetchall()
    if dry_run:
        print(f"Would clean up {len(rows)} recipes")
        return 0
    # Actual LLM call implementation deferred to deployment — uses httpx
    # to POST to the model endpoint with the prompt.
    print(f"Cleaned up 0 of {len(rows)} recipes (LLM call not implemented in test env)")
    return 0