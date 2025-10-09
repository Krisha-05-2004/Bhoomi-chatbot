from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("API key not found. Please check your .env file.")
