from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any  
import json
import os
import re 
import random  
from datetime import datetime  
from services.report_service import generate_weekly_report


# Import from new structure
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

# Serve static files from CURRENT directory (where main.py is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Debug: Print paths to verify
print(f"Current file: {__file__}")
print(f"BASE_DIR: {BASE_DIR}")
print(f"Files in current directory: {os.listdir(BASE_DIR)}")

# ============== API ENDPOINTS FIRST (to avoid conflicts) ==============

# Request/Response Models
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


# Endpoints - PUT THESE BEFORE STATIC FILE ROUTES
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


# Add this to your main.py after the other endpoints

@app.get("/debug/report-test/{username}")
async def debug_report_test(username: str):
    """Debug endpoint to test report generation"""
    try:
        from services.report_service import generate_weekly_report
        report = generate_weekly_report(username)
        return {
            "status": "success",
            "report": report,
            "message": "Report generated successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate report"
        }

@app.get("/debug/user-mood-data/{username}")
async def debug_user_mood_data(username: str):
    """Debug endpoint to check user mood data"""
    from database import get_user_mood_history, get_user
    
    user = get_user(username)
    mood_history = get_user_mood_history(username)
    
    return {
        "user_exists": user is not None,
        "mood_entries_count": len(mood_history),
        "recent_entries": mood_history[:5] if mood_history else [],
        "all_moods": [entry['mood'] for entry in mood_history] if mood_history else []
    }

@app.post("/chat/end/{session_id}")
async def end_chat(session_id: int):
    """
    End a chat session.
    """
    end_chat_session(session_id)
    return {"status": "success", "message": "Chat session ended"}

@app.get("/simple-report/{username}")
async def get_simple_report(username: str):
    """
    Simple fallback report endpoint
    """
    from database import get_user_mood_history, get_user
    
    username = username.strip()
    
    if not user_exists(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Get user's mood history
        mood_history = get_user_mood_history(username)
        
        # Create a simple report
        mood_distribution = {}
        for entry in mood_history:
            mood = entry['mood']
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
        
        # Generate simple insights
        insights = []
        if mood_history:
            latest_mood = mood_history[0]['mood']
            insights.append(f"Your current mood is: {latest_mood}")
            insights.append(f"Total assessments completed: {len(mood_history)}")
        else:
            insights.append("No mood data yet. Complete an assessment!")
        
        # Simple recommendations
        recommendations = [
            "Track your mood regularly for better insights",
            "Practice self-care daily",
            "Stay connected with supportive people",
            "Get adequate sleep and nutrition"
        ]
        
        return {
            "username": username,
            "period": "All Time Data",
            "total_entries": len(mood_history),
            "mood_distribution": mood_distribution,
            "insights": insights,
            "recommendations": recommendations,
            "mood_trend": "Baseline established" if mood_history else "New user"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating simple report: {str(e)}")

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

# ============== CHATBOT ENDPOINTS ==============

CHATBOT_INTENTS = {
    "greeting": {
        "patterns": [r"\bhi\b", r"\bhello\b", r"\bhey\b", r"assalam"],
        "responses": [
            "Hello! How can I support you today?",
            "Hey there! What's on your mind?",
            "Hi! I'm here to help whenever you're ready."
        ]
    },
    "sadness": {
        "patterns": [r"\bsad\b", r"\bdepressed\b", r"\bdown\b", r"\bunhappy\b"],
        "responses": [
            "I'm really sorry you're feeling this way. Want to share what's troubling you?",
            "That sounds hard… I'm here for you. What happened?",
            "It's okay to feel this way. Tell me more, I'm listening."
        ]
    },
    "anxiety": {
        "patterns": [r"\banxious\b", r"\banxiety\b", r"\bscared\b", r"\bworried\b"],
        "responses": [
            "Anxiety can be overwhelming. Do you know what triggered it?",
            "You're safe. Let's work through this. What are you worried about?",
            "Take a breath… I'm right here. Want to talk about what's making you anxious?"
        ]
    },
    "stress": {
        "patterns": [r"\bstress\b", r"\bstressed\b", r"\boverwhelmed\b", r"\bpressure\b"],
        "responses": [
            "Stress can feel overwhelming. Let's break this down together.",
            "I hear you're feeling stressed. What's causing the most pressure right now?",
            "Stress is tough. Would it help to talk about what's overwhelming you?"
        ]
    },
    "sleep": {
        "patterns": [r"\bsleep\b", r"\btired\b", r"\binsomnia\b", r"\bexhausted\b"],
        "responses": [
            "Sleep issues can really affect your wellbeing. How's your sleep been lately?",
            "Feeling tired can make everything harder. Are you getting enough rest?",
            "Sleep is so important for mental health. What's your sleep pattern been like?"
        ]
    },
    "goodbye": {
        "patterns": [r"\bbye\b", r"\bgoodbye\b", r"\bsee you\b", r"\bgood night\b"],
        "responses": [
            "Take care! I'm always here if you need me.",
            "Goodbye! Remember, you're doing your best.",
            "See you soon. Stay strong!"
        ]
    }
}

class ChatbotRequest(BaseModel):
    user_id: Optional[str] = None
    message: str
    metadata: Optional[Dict[str, Any]] = None

class ChatbotResponse(BaseModel):
    user_id: Optional[str]
    message: str
    intent: str
    timestamp: str
    bot_reply: str
    confidence: float

def classify_chatbot_intent(message: str) -> (str, float):
    """
    Simple regex-based intent classification for the chatbot
    """
    message = message.lower()
    
    for intent_name, data in CHATBOT_INTENTS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, message, re.IGNORECASE):
                return intent_name, 0.9
    
    # Fallback: check for keywords
    for intent_name, data in CHATBOT_INTENTS.items():
        for pattern in data["patterns"]:
            keyword = re.sub(r"[^\w\s]", "", pattern)
            if keyword and keyword.strip() and keyword.strip() in message:
                return intent_name, 0.6
    
    return "general", 0.3

def generate_chatbot_reply(intent: str, user_message: str) -> str:
    """
    Generate response based on intent
    """
    if intent in CHATBOT_INTENTS:
        return random.choice(CHATBOT_INTENTS[intent]["responses"])
    
    # Fallback empathetic responses
    fallback_responses = [
        "I understand... please tell me more about how you're feeling.",
        "Thank you for sharing that with me. Would you like to explore this further?",
        "I'm listening carefully. Could you tell me more about what's on your mind?",
        "That sounds important. How has this been affecting you?",
        "I appreciate you opening up about this. What would help you feel better?",
        "Let's work through this together. What do you think might help?"
    ]
    return random.choice(fallback_responses)

@app.post("/chatbot/message", response_model=ChatbotResponse)
async def chatbot_message(request: ChatbotRequest):
    """
    Simple chatbot endpoint that works independently of the main psychiatrist chat
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Classify intent and generate response
    intent, confidence = classify_chatbot_intent(request.message)
    bot_reply = generate_chatbot_reply(intent, request.message)
    timestamp = datetime.utcnow().isoformat()

    return ChatbotResponse(
        user_id=request.user_id,
        message=request.message,
        intent=intent,
        timestamp=timestamp,
        bot_reply=bot_reply,
        confidence=confidence
    )

@app.get("/chatbot/intents")
async def get_chatbot_intents():
    """Get list of available intents"""
    return {"intents": list(CHATBOT_INTENTS.keys())}


# ============== STATIC FILE ROUTES (PUT THESE LAST) ==============

# Serve static files (JS, CSS, HTML) - PUT THESE AFTER API ENDPOINTS
@app.get("/")
async def serve_login():
    """Serve the login page as default."""
    return FileResponse(os.path.join(BASE_DIR, "login.html"))

@app.get("/login")
async def serve_login_page():
    """Serve the login page."""
    return FileResponse(os.path.join(BASE_DIR, "login.html"))

@app.get("/questions")
async def serve_questions():
    """Serve the questions page."""
    return FileResponse(os.path.join(BASE_DIR, "login.html"))

@app.get("/results")
async def serve_results():
    """Serve the results page."""
    return FileResponse(os.path.join(BASE_DIR, "results.html"))

@app.get("/report")
async def serve_report():
    """Serve the weekly report page."""
    return FileResponse(os.path.join(BASE_DIR, "report.html"))

@app.get("/chat")
async def serve_chat():
    """Serve the chat page."""
    return FileResponse(os.path.join(BASE_DIR, "chat.html"))

# Serve JS files
@app.get("/{filename}.js")
async def serve_js(filename: str):
    """Serve JavaScript files."""
    js_files = ["questions", "results", "report", "chat"]
    if filename in js_files:
        file_path = os.path.join(BASE_DIR, f"{filename}.js")
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="File not found")

# Serve CSS files
@app.get("/styles.css")
async def serve_css():
    """Serve CSS files."""
    file_path = os.path.join(BASE_DIR, "styles.css")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="File not found")

# Serve assets
@app.get("/assets/{asset_path:path}")
async def serve_assets(asset_path: str):
    """Serve assets from the assets folder."""
    asset_file_path = os.path.join(BASE_DIR, "assets", asset_path)
    if os.path.exists(asset_file_path):
        return FileResponse(asset_file_path)
    raise HTTPException(status_code=404, detail="Asset not found")


@app.get("/{filename}.html")
async def serve_html(filename: str):
    """Serve HTML files."""
    html_files = ["login", "results", "report", "chat"]
    if filename in html_files:
        file_path = os.path.join(BASE_DIR, f"{filename}.html")
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/debug/user-data")
async def debug_user_data():
    """Debug endpoint to check user data in localStorage"""
    return {
        "message": "Debug endpoint working",
        "test_data": {
            "currentUser": "test_user",
            "currentMoodLogId": 1
        }
    }

@app.post("/test/chat-start")
async def test_chat_start():
    """Test endpoint for chat start"""
    return {
        "session_id": 999,
        "greeting": "Hello! This is a test greeting from NeuroCare AI. How are you feeling today?",
        "mood": "Test Mood"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)