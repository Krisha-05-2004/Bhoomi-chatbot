from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
MAX_HISTORY = 5
