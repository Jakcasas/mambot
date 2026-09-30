"""Configuration comes from the process environment; no source ZIP credentials."""
from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.1.0'

@dataclass(frozen=True)
class Settings:
    data_mode: str = os.getenv('MAMBOT_DATA_MODE', 'local')
    mongo_uri: str = os.getenv('MONGODB_URI', '')
    mongo_database: str = os.getenv('MONGODB_DATABASE', 'huit_chatbot')
    vector_enabled: bool = os.getenv('MAMBOT_VECTOR_ENABLED', '0') == '1'
    llm_key: str = os.getenv('OPENROUTER_API_KEY', '')
    llm_model: str = os.getenv('OPENROUTER_MODEL', '')
    audit_path: Path = Path(os.getenv('MAMBOT_AUDIT_PATH', str(ROOT / 'var' / 'operations.jsonl')))

settings = Settings()
