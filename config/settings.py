import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Settings
CACHE_DIR = ".bib_cache"
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

