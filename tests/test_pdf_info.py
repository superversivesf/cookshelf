import os
import pytest
from cooksLibrary.ingest.pdf_info import extract_info

REAL_PDF = "/path/to/cookbooks/Weekend Cooking/eatlikeamanguidetofeedingacrowd.pdf"

pytestmark = pytest.mark.skipif(
    not os.path.exists(REAL_PDF),
    reason="Real test PDF not available"
)

def test_extract_info():
    info = extract_info(REAL_PDF)
    assert info["page_count"] == 226
    assert info["title"] == "The Eat Like a Man Guide to Feeding a Crowd"
    assert info["author"] == "D'Agostino Voltaggio Batali Granger"