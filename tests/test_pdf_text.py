import os
import pytest
from pathlib import Path
from cooksLibrary.ingest.pdf_text import extract_page, extract_pages

REAL_PDF = "/mnt/media/Komga/Cooking/Weekend Cooking/eatlikeamanguidetofeedingacrowd.pdf"

pytestmark = pytest.mark.skipif(
    not os.path.exists(REAL_PDF),
    reason="Real test PDF not available"
)

def test_extract_page_returns_text(tmp_data_dir):
    text = extract_page(REAL_PDF, 14, tmp_data_dir)
    assert "Waffles" in text
    assert len(text) > 100

def test_extract_page_caches(tmp_data_dir):
    text1 = extract_page(REAL_PDF, 14, tmp_data_dir)
    cache_file = tmp_data_dir / "text_cache" / "eatlikeamanguidetofeedingacrowd" / "0014.txt"
    assert cache_file.exists()
    text2 = extract_page(REAL_PDF, 14, tmp_data_dir)
    assert text1 == text2

def test_extract_pages_range(tmp_data_dir):
    text = extract_pages(REAL_PDF, 14, 16, tmp_data_dir)
    assert "Waffles" in text
    assert len(text) > len(extract_page(REAL_PDF, 14, tmp_data_dir))