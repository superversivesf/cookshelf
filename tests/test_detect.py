import os
import pytest
from pathlib import Path
from unittest.mock import patch
from cooksLibrary.ingest.detect import detect_recipes, filter_outline_entries, _detect_page_walk

REAL_PDF = "/path/to/cookbooks/Weekend Cooking/eatlikeamanguidetofeedingacrowd.pdf"

pytestmark = pytest.mark.skipif(
    not os.path.exists(REAL_PDF),
    reason="Real test PDF not available"
)

def test_detect_from_outline(tmp_data_dir):
    recipes = detect_recipes(REAL_PDF, tmp_data_dir, outline_present=True)
    assert len(recipes) > 10
    titles = [r["title"] for r in recipes]
    assert any("Waffles" in t for t in titles)
    assert all(r["page_start"] >= 1 for r in recipes)

def test_filter_stops_non_recipe_entries():
    entries = [
        ("Cover", 0), ("Title", 2), ("Copyright", 3), ("Contents", 4),
        ("FOREWORD", 6), ("Waffles and Eggs", 13), ("How to Feed an Army", 17),
        ("INDEX", 217), ("Credits", 223),
        ("A", 217), ("B", 217), ("E", 219), ("Z", 222),
    ]
    filtered = filter_outline_entries(entries)
    titles = [e[0] for e in filtered]
    assert "Waffles and Eggs" in titles
    assert "Cover" not in titles
    assert "INDEX" not in titles
    assert "How to Feed an Army" not in titles  # "How to" sidebar
    assert "A" not in titles  # single-letter index headings
    assert "B" not in titles
    assert "Z" not in titles

def test_page_walk_assigns_correct_titles(tmp_data_dir):
    pages = {
        1: "Intro\nSome text without serves marker.",
        2: "First Recipe\nServes 4\nSome instructions here.",
        3: "Continued instructions from previous recipe.",
        4: "Second Recipe\nServes 6\nMore instructions.",
        5: "Third Recipe\nMAKES 8\nFinal instructions.",
    }
    def fake_extract_page(pdf_path, page, cache_dir, **kwargs):
        return pages.get(page, "")
    class FakeReader:
        @property
        def pages(self):
            return list(range(5))
    with patch("cooksLibrary.ingest.detect.extract_page", side_effect=fake_extract_page), \
         patch("cooksLibrary.ingest.detect.pypdf.PdfReader", return_value=FakeReader()):
        recipes = _detect_page_walk("/fake.pdf", tmp_data_dir)
    assert len(recipes) == 3
    assert recipes[0]["title"] == "First Recipe"
    assert recipes[0]["page_start"] == 2
    assert recipes[0]["page_end"] == 3
    assert recipes[1]["title"] == "Second Recipe"
    assert recipes[1]["page_start"] == 4
    assert recipes[1]["page_end"] == 4
    assert recipes[2]["title"] == "Third Recipe"
    assert recipes[2]["page_start"] == 5
    assert recipes[2]["page_end"] == 5