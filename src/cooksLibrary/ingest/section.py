import re
from .ingredients import parse_line

SERVES_RE = re.compile(
    r"(?:SERVES|Serves|serves|MAKES|Makes)\s+(\d+)(?:\s*(?:to|-|\u2013)\s*(\d+))?"
)
SECTION_HEADER_RE = re.compile(r"^[A-Z][A-Z\s&]{2,}:?\s*$")

def section_recipe(text: str, title: str) -> dict:
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    # Drop the title line if it's the first non-empty line (prefix match —
    # the title arg may be shorter than the full title on the page)
    if lines and title and lines[0].strip().startswith(title.strip()):
        lines = lines[1:]

    description_parts = []
    ingredients = []
    instructions_parts = []
    current_section = ""
    in_ingredients = False
    in_instructions = False

    for line in lines:
        stripped = line.strip()
        serves_match = SERVES_RE.search(stripped)
        if serves_match:
            s_min = int(serves_match.group(1))
            s_max = int(serves_match.group(2)) if serves_match.group(2) else s_min
            continue
        if SECTION_HEADER_RE.match(stripped) and not in_instructions:
            current_section = stripped.rstrip(":")
            in_ingredients = True
            continue
        parsed = parse_line(stripped)
        if parsed and not in_instructions:
            in_ingredients = True
            ingredients.append({"section": current_section, "line": stripped, "parsed": parsed})
            continue
        if in_ingredients and not parsed and len(stripped) > 50:
            in_instructions = True
        if in_instructions:
            instructions_parts.append(stripped)
        elif not in_ingredients:
            description_parts.append(stripped)

    servings_match = SERVES_RE.search(text)
    if servings_match:
        s_min = int(servings_match.group(1))
        s_max = int(servings_match.group(2)) if servings_match.group(2) else s_min
        servings_str = servings_match.group(1)
    else:
        servings_str = None
        s_min = None
        s_max = None

    return {
        "description": "\n".join(description_parts).strip() or None,
        "ingredients": ingredients,
        "instructions": "\n\n".join(instructions_parts).strip() or None,
        "servings": servings_str,
        "servings_min": s_min,
        "servings_max": s_max,
    }