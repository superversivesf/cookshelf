def score_recipe(recipe: dict) -> tuple[float, str]:
    score = 0.0
    notes = []
    title = recipe.get("title", "")
    if title and len(title) < 80:
        score += 0.30
    else:
        notes.append("title missing or too long")
    if recipe.get("servings"):
        score += 0.20
    else:
        notes.append("no servings")
    ingredients = recipe.get("ingredients", [])
    if len(ingredients) >= 3:
        score += 0.20
    else:
        notes.append("few ingredients")
    instructions = recipe.get("instructions") or ""
    if len(instructions) >= 50:
        score += 0.15
    else:
        notes.append("short instructions")
    if ingredients:
        with_units = sum(1 for i in ingredients if i.get("parsed", {}).get("unit"))
        if with_units / max(len(ingredients), 1) > 0.3:
            score += 0.10
    return min(score, 1.0), "; ".join(notes)