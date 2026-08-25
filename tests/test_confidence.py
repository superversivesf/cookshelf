from cooksLibrary.ingest.confidence import score_recipe

def test_high_confidence_well_parsed():
    recipe = {
        "title": "Test Recipe",
        "description": "A description",
        "ingredients": [{"section": "", "line": "2 cups flour"},
                        {"section": "", "line": "1 tsp salt"},
                        {"section": "", "line": "3 eggs"}],
        "instructions": "Mix well and bake for 30 minutes until golden brown.",
        "servings": "4", "servings_min": 4, "servings_max": 4,
    }
    score, notes = score_recipe(recipe)
    assert score >= 0.6
    assert notes == ""

def test_low_confidence_no_servings():
    recipe = {
        "title": "T",
        "description": "",
        "ingredients": [],
        "instructions": "short",
        "servings": None, "servings_min": None, "servings_max": None,
    }
    score, notes = score_recipe(recipe)
    assert score < 0.6
    assert "servings" in notes