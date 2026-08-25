import os
from dataclasses import dataclass

@dataclass
class Settings:
    library_path: list[str]
    db_path: str
    data_dir: str
    confidence_threshold: float
    categories_file: str
    llm_model: str | None
    llm_api_key: str | None

def get_settings() -> Settings:
    library_path = os.environ.get("COOKS_LIBRARY_PATH", "/library/existing:/library/incoming")
    return Settings(
        library_path=library_path.split(":"),
        db_path=os.environ.get("COOKS_DB_PATH", "/data/cooks.db"),
        data_dir=os.environ.get("COOKS_DATA_DIR", "/data"),
        confidence_threshold=float(os.environ.get("COOKS_CONFIDENCE_THRESHOLD", "0.6")),
        categories_file=os.environ.get("COOKS_CATEGORIES_FILE", "/data/categories.yml"),
        llm_model=os.environ.get("COOKS_LLM_MODEL"),
        llm_api_key=os.environ.get("COOKS_LLM_API_KEY"),
    )