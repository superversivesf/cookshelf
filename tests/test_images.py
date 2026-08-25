import os
import pytest
from pathlib import Path
from cooksLibrary.ingest.images import page_image_path


def test_page_image_path(tmp_data_dir):
    p = page_image_path("test-book", 5, tmp_data_dir)
    assert "test-book" in str(p)
    assert "0005.webp" in str(p)
    assert p.parent.exists()