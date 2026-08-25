from unittest.mock import patch, MagicMock
from cooksLibrary.ingest.llm_cleanup import build_prompt, parse_llm_response

def test_build_prompt_contains_recipe_text():
    prompt = build_prompt("Cake", "2 cups flour\n1 egg", "Mix and bake.")
    assert "Cake" in prompt
    assert "2 cups flour" in prompt
    assert "JSON" in prompt

def test_parse_llm_response_valid():
    json_str = '{"title": "Cake", "servings": "8", "ingredients": [{"quantity": "2", "unit": "cups", "name": "flour", "note": ""}], "instructions": "Mix."}'
    result = parse_llm_response(json_str)
    assert result["title"] == "Cake"
    assert len(result["ingredients"]) == 1

def test_parse_llm_response_invalid():
    result = parse_llm_response("not json at all")
    assert result is None

def test_parse_llm_response_missing_fields():
    result = parse_llm_response('{"title": "Cake"}')
    assert result is None