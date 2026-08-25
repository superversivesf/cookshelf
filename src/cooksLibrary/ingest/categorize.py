import yaml

def load_categories(path: str) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("categories", [])

def categorize_book(book: dict, early_text: str, filename: str,
                    folder: str, categories: list[dict]) -> str:
    scores = {c["name"]: 0 for c in categories}
    metadata_text = " ".join(filter(None, [book.get("title"), book.get("author")])).lower()
    signals = [
        (metadata_text, 3),
        (early_text.lower(), 2),
        (filename.lower(), 1),
        (folder.lower(), 1),
    ]
    for cat in categories:
        for keyword in cat["keywords"]:
            kw = keyword.lower()
            for text, weight in signals:
                count = text.count(kw)
                if count:
                    scores[cat["name"]] += count * cat["weight"] * weight
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Uncategorized"
    return best