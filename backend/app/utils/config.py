import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mood_tracker.db")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-oss:20b-cloud")

settings = Settings()