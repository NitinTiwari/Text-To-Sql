# Global configuration loaded from .env
import os
from pathlib import Path

# Base directory is the project root (where this file is located)
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
dotenv_path = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)
except ImportError:
    # Built-in fallback parser if python-dotenv is not installed in the current environment
    if dotenv_path.is_file():
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val

# Database file path (absolute or relative to project root)
DB_FILE = os.getenv("DB_FILE", "amazon.db")
if not Path(DB_FILE).is_absolute():
    DB_FILE = str(BASE_DIR / DB_FILE)

# Ollama base URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Default model for Text-to-SQL
TEXT_TO_SQL_MODEL = os.getenv("TEXT_TO_SQL_MODEL", "llama3.1:latest")

# FastAPI backend URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
