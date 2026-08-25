from cooksLibrary.config import get_settings

def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("COOKS_LIBRARY_PATH", "/library/existing:/library/incoming")
    monkeypatch.setenv("COOKS_DB_PATH", "/data/cooks.db")
    monkeypatch.setenv("COOKS_DATA_DIR", "/data")
    monkeypatch.setenv("COOKS_CONFIDENCE_THRESHOLD", "0.6")
    monkeypatch.setenv("COOKS_CATEGORIES_FILE", "/data/categories.yml")
    s = get_settings()
    assert s.library_path == ["/library/existing", "/library/incoming"]
    assert s.db_path == "/data/cooks.db"
    assert s.data_dir == "/data"
    assert s.confidence_threshold == 0.6
    assert s.categories_file == "/data/categories.yml"
    assert s.llm_model is None
    assert s.llm_api_key is None