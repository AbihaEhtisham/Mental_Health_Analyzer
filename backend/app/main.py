from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from typing import Dict, List, Optional
import json
import os

# Import from new structure - NO CHANGES NEEDED since files are in same folder
from LLM_logic_for_mood_detection import query_mood_model
from LLM_logic_for_psychiatrist import chat_with_psychiatrist, get_initial_greeting
from prompt_for_mood_detection import system_prompt
from database import (
    create_user,
    get_user,
    user_exists,
    save_mood_log,
    get_user_mood_history,
    create_chat_session,
    end_chat_session,
    save_chat_message,
    get_session_messages,
    get_user_chat_sessions,
    get_latest_mood_log
)

# Import the new report service
from services.report_service import generate_weekly_report

app = FastAPI(title="Mental Health Analyzer API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend directory - CORRECTED PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main HTML page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Request/Response Models - MOVED TO SEPARATE FILES BUT KEEPING HERE FOR COMPATIBILITY
class SignupRequest(BaseModel):
    username: str


class LoginRequest(BaseModel):
    username: str


class MoodDetectRequest(BaseModel):
    username: str
    answers: Dict[str, str]


class UserResponse(BaseModel):
    username: str
    status: str
    message: str


class MoodResponse(BaseModel):
    mood: str
    status: str
    log_id: int


class MoodHistoryItem(BaseModel):
    id: int
    mood: str
    answers: Dict[str, str]
    created_at: str


class MoodHistoryResponse(BaseModel):
    username: str
    total_entries: int
    history: List[MoodHistoryItem]


# NEW: Weekly Report Models
class WeeklyReportResponse(BaseModel):
    username: str
    period: str
    total_entries: int
    mood_distribution: Dict[str, int]
    insights: List[str]
    recommendations: List[str]
    mood_trend: str


# Endpoints
@app.post("/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """
    Register a new user with a unique username.
    """
    username = request.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    if user_exists(username):
        raise HTTPException(status_code=409, detail="Username already exists. Please login instead.")

    user_id = create_user(username)

    if user_id is None:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return UserResponse(
        username=username,
        status="success",
        message="User registered successfully"
    )


@app.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """
    Login with an existing username.
    """
    username = request.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    user = get_user(username)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Please signup first.")

    return UserResponse(
        username=username,
        status="success",
        message="Login successful"
    )


@app.post("/detect-mood", response_model=MoodResponse)
async def detect_mood(request: MoodDetectRequest):
    """
    Takes username and 10 MCQ answers (q1-q10), detects mood, and saves to database.

    Example input:
    {
        "username": "john_doe",
        "answers": {"q1": "A", "q2": "C", "q3": "E", ...}
    }
    """
    username = request.username.strip()
    answers = request.answers

    # Validate user exists
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Please signup first.")

    # Detect mood
    mood = query_mood_model(answers, system_prompt)

    if mood is None:
        raise HTTPException(status_code=500, detail="Failed to detect mood from model")

    # Save to database
    log_id = save_mood_log(
        user_id=user["id"],
        mood=mood,
        answers=json.dumps(answers)
    )

    return MoodResponse(mood=mood, status="success", log_id=log_id)


@app.get("/mood-history/{username}", response_model=MoodHistoryResponse)
async def get_mood_history(username: str):
    """
    Get all mood history for a user.
    """
    username = username.strip()

    if not user_exists(username):
        raise HTTPException(status_code=404, detail="User not found")

    history = get_user_mood_history(username)

    # Parse answers JSON for each entry
    history_items = [
        MoodHistoryItem(
            id=item["id"],
            mood=item["mood"],
            answers=json.loads(item["answers"]),
            created_at=item["created_at"]
        )
        for item in history
    ]

    return MoodHistoryResponse(
        username=username,
        total_entries=len(history_items),
        history=history_items
    )


@app.get("/check-user/{username}")
async def check_user(username: str):
    """
    Check if a username exists (for app flow: signup vs login).
    """
    exists = user_exists(username.strip())
    return {
        "username": username,
        "exists": exists,
        "action": "login" if exists else "signup"
    }


# ============== CHAT/PSYCHIATRIST ENDPOINTS ==============

class StartChatRequest(BaseModel):
    username: str
    mood_log_id: int


class StartChatResponse(BaseModel):
    session_id: int
    greeting: str
    mood: str


class ChatMessageRequest(BaseModel):
    session_id: int
    message: str


class ChatMessageResponse(BaseModel):
    response: str
    message_id: int


class ChatMessage(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


class ChatSessionInfo(BaseModel):
    id: int
    mood: str
    started_at: str
    ended_at: Optional[str]


@app.post("/chat/start", response_model=StartChatResponse)
async def start_chat_session(request: StartChatRequest):
    """
    Start a new chat session with the psychiatrist.
    Requires the mood_log_id from a completed mood detection.
    """
    username = request.username.strip()

    # Validate user
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Get mood history for context
    mood_history = get_user_mood_history(username)

    # Find the current mood from the mood_log_id
    current_mood = None
    for entry in mood_history:
        if entry["id"] == request.mood_log_id:
            current_mood = entry["mood"]
            break

    if current_mood is None:
        raise HTTPException(status_code=404, detail="Mood log not found")

    # Create chat session
    session_id = create_chat_session(user["id"], request.mood_log_id)

    # Get initial greeting from psychiatrist
    greeting = get_initial_greeting(current_mood, mood_history)

    if greeting is None:
        greeting = f"Hello! I'm Dr. Mira, your AI wellness companion. I see you're feeling {current_mood} today. I'm here to listen and support you. How are you doing right now?"

    # Save the greeting as first message
    save_chat_message(session_id, "assistant", greeting)

    return StartChatResponse(
        session_id=session_id,
        greeting=greeting,
        mood=current_mood
    )


@app.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageRequest):
    """
    Send a message to the psychiatrist and get a response.
    """
    session_id = request.session_id
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get session info to find user and mood
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cs.user_id, cs.mood_log_id, ml.mood, u.username
        FROM chat_sessions cs
        JOIN mood_logs ml ON cs.mood_log_id = ml.id
        JOIN users u ON cs.user_id = u.id
        WHERE cs.id = ?
    """, (session_id,))
    session_info = cursor.fetchone()
    conn.close()

    if session_info is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    username = session_info["username"]
    current_mood = session_info["mood"]

    # Save user message
    save_chat_message(session_id, "user", user_message)

    # Get conversation history
    messages = get_session_messages(session_id)

    # Get mood history for context
    mood_history = get_user_mood_history(username)

    # Get response from psychiatrist
    response = chat_with_psychiatrist(
        user_message=user_message,
        current_mood=current_mood,
        mood_history=mood_history,
        conversation_history=messages[:-1]  # Exclude the message we just added
    )

    if response is None:
        response = "I apologize, but I'm having a moment of difficulty. Could you please repeat what you said? I want to make sure I understand you correctly."

    # Save assistant response
    message_id = save_chat_message(session_id, "assistant", response)

    return ChatMessageResponse(response=response, message_id=message_id)


@app.post("/chat/end/{session_id}")
async def end_chat(session_id: int):
    """
    End a chat session.
    """
    end_chat_session(session_id)
    return {"status": "success", "message": "Chat session ended"}


@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: int):
    """
    Get all messages from a chat session.
    """
    messages = get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages
    }


@app.get("/chat/sessions/{username}")
async def get_user_sessions(username: str):
    """
    Get all chat sessions for a user.
    """
    if not user_exists(username.strip()):
        raise HTTPException(status_code=404, detail="User not found")

    sessions = get_user_chat_sessions(username)
    return {
        "username": username,
        "sessions": sessions
    }


# ============== NEW WEEKLY REPORT ENDPOINT ==============

@app.get("/weekly-report/{username}", response_model=WeeklyReportResponse)
async def get_weekly_report(username: str):
    """
    Get weekly mood report with insights and personalized recommendations.
    """
    username = username.strip()
    
    if not user_exists(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        report = generate_weekly_report(username)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)