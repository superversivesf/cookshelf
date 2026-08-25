from cooksLibrary.ingest.categorize import categorize_book, load_categories

CATEGORIES = [
    {"name": "Instant Pot & Pressure Cooking",
     "keywords": ["instant pot", "pressure cooker"], "weight": 10},
    {"name": "Desserts & Baking",
     "keywords": ["dessert", "cake", "cookie", "baking", "cheesecake"], "weight": 5},
    {"name": "Cocktails & Drinks",
     "keywords": ["cocktail", "martini", "bourbon", "whiskey"], "weight": 10},
]

def test_metadata_title_match_dominates():
    book = {"title": "The Instant Pot Desserts Cookbook", "author": None}
    result = categorize_book(book, "", "instantpotdesserts.pdf", "William Sonoma", CATEGORIES)
    assert result == "Instant Pot & Pressure Cooking"

def test_early_text_match():
    book = {"title": "Untitled", "author": None}
    early_text = "This book is all about cheesecake and cake baking."
    result = categorize_book(book, early_text, "somebook.pdf", "Misc", CATEGORIES)
    assert result == "Desserts & Baking"

def test_no_match_returns_uncategorized():
    book = {"title": "Unknown Book", "author": None}
    result = categorize_book(book, "", "unknown.pdf", "Misc", CATEGORIES)
    assert result == "Uncategorized"

def test_folder_name_as_fallback():
    book = {"title": "Untitled", "author": None}
    categories = CATEGORIES + [
        {"name": "Weekend Cooking", "keywords": ["weekend cooking"], "weight": 5},
    ]
    result = categorize_book(book, "", "somebook.pdf", "Weekend Cooking", categories)
    assert result == "Weekend Cooking"