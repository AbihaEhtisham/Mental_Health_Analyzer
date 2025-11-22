import requests
import json
import os
from typing import Optional, Dict
from dotenv import load_dotenv
from prompt_for_mood_detection import system_prompt

# Load environment variables from .env
load_dotenv()

MODEL = "gpt-oss:20b-cloud"  # e.g., "llama3.1:latest"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

def query_mood_model(answers: Dict[str, str], system_prompt: str) -> Optional[str]:
    """
    Sends the 10-question answers to your Ollama model and returns ONE WORD (mood).
    """

    # Prepare messages for Ollama
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(answers)}
    ]

    # Headers with API key
    headers = {
        "Content-Type": "application/json"
    }
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    try:
        response = requests.post(
            OLLAMA_URL,
            headers=headers,
            json={
                "model": MODEL,
                "messages": messages,
                "options": {
                    "seed": 42,
                    "temperature": 0.1
                }
            },
            stream=False
        )
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

    # Raw streaming-like output (Ollama returns JSON lines)
    raw_lines = response.text.strip().split("\n")
    full_output = ""

    for line in raw_lines:
        if not line.strip():
            continue

        try:
            data = json.loads(line)
            msg = data.get("message", {})
            content = msg.get("content", "")

            if content:
                full_output += content.strip()

            # When "done": true → stop
            if data.get("done", False):
                break

        except json.JSONDecodeError:
            continue

    full_output = full_output.strip()

    # Validate against allowed categories (5 mood system)
    allowed_moods = {
        "Happy/Calm",
        "Neutral",
        "Stressed",
        "Depressed/Low",
        "Tired/Exhausted"
    }

    # Check if the output matches any allowed mood
    mood = None
    for allowed in allowed_moods:
        if full_output.lower() == allowed.lower() or full_output.lower().startswith(allowed.lower().split('/')[0]):
            mood = allowed
            break

    # Ensure output is an allowed mood
    if mood is None:
        print(f"Unexpected response from model: {full_output}")
        return None

    return mood
