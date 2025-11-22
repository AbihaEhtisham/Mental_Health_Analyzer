import requests
import json
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv
from prompt_for_psychiatrist import get_psychiatrist_prompt

# Load environment variables from .env
load_dotenv()

MODEL = "gpt-oss:20b-cloud"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")


def chat_with_psychiatrist(
    user_message: str,
    current_mood: str,
    mood_history: List[Dict],
    conversation_history: List[Dict]
) -> Optional[str]:
    """
    Send a message to the psychiatrist chatbot and get a response.

    Args:
        user_message: The user's current message
        current_mood: The user's detected mood for this session
        mood_history: List of previous mood logs
        conversation_history: List of previous messages in this session

    Returns:
        The psychiatrist's response or None if error
    """

    # Generate system prompt with mood context
    system_prompt = get_psychiatrist_prompt(current_mood, mood_history)

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Headers with API key
    headers = {"Content-Type": "application/json"}
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
                    "temperature": 0.5,
                    "num_predict": 150
                }
            },
            stream=False,
            timeout=60
        )
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

    # Parse response (Ollama returns JSON lines)
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
                full_output += content

            if data.get("done", False):
                break

        except json.JSONDecodeError:
            continue

    return full_output.strip() if full_output else None


def get_initial_greeting(current_mood: str, mood_history: List[Dict]) -> Optional[str]:
    """
    Get the initial greeting from the psychiatrist when starting a session.
    """

    # Create a prompt for initial greeting
    system_prompt = get_psychiatrist_prompt(current_mood, mood_history)

    initial_prompt = """Say hi and ask how they're doing. 2-3 sentences MAX. One question only."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_prompt}
    ]

    headers = {"Content-Type": "application/json"}
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
                    "temperature": 0.5,
                    "num_predict": 150
                }
            },
            stream=False,
            timeout=60
        )
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

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
                full_output += content

            if data.get("done", False):
                break

        except json.JSONDecodeError:
            continue

    return full_output.strip() if full_output else None
