import re

# Unicode-aware fraction characters
FRACTION = r"(?:\d+\s+\d+/\d+|\d+\s+[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+/\d+|\d+(?:\.\d+)?|[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])"

UNITS = (
    r"cups?|tbsp|tablespoons?|tsp|teaspoons?|oz|ounces?|lb|lbs|pounds?|"
    r"kg|g\b|ml|l\b|liters?|cans?|packages?|cloves?|sticks?|sprigs?|"
    r"bunches?|pinches?|slices?|pieces?"
)

# Section headers like "FOR THE CRUST", "CRUST:", "FILLING"
SECTION_RE = re.compile(r"^[A-Z\s]{2,}:?\s*$")

# Dual-unit suffix like "/300 ml" or "/60 g" — stripped from ingredient name
DUAL_UNIT_RE = re.compile(r"/\s*\d+(?:\.\d+)?\s*(?:ml|g|kg|oz|lb)\b", re.IGNORECASE)

INGREDIENT_RE = re.compile(
    rf"^(?P<qty>{FRACTION})\s*"
    rf"(?P<unit>{UNITS})?\s*"
    rf"(?P<name>.+?)(?:,\s*(?P<note>.*))?$"
)

def parse_line(raw: str) -> dict | None:
    line = raw.strip()
    if not line:
        return None
    if SECTION_RE.match(line):
        return None
    # Strip dual-unit suffixes from the line before matching
    cleaned = DUAL_UNIT_RE.sub("", line).strip()
    m = INGREDIENT_RE.match(cleaned)
    if not m:
        return None
    return {
        "quantity": m.group("qty").strip(),
        "unit": (m.group("unit") or "").strip(),
        "ingredient_name": m.group("name").strip(),
        "note": (m.group("note") or "").strip(),
        "raw_text": raw.strip(),
    }