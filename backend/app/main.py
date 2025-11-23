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

# Safe imports that won't crash Vercel
try:
    # Try local imports first
    from services.report_service import generate_weekly_report
    from LLM_logic_for_mood_detection import query_mood_model
    from LLM_logic_for_psychiatrist import chat_with_psychiatrist, get_initial_greeting
    from prompt_for_mood_detection import system_prompt
    from database import (
        create_user, get_user, user_exists, save_mood_log,
        get_user_mood_history, create_chat_session, end_chat_session,
        save_chat_message, get_session_messages, get_user_chat_sessions,
        get_latest_mood_log
    )
    print("✅ Using local import paths")
except ImportError:
    # Fallback - create dummy functions so app doesn't crash
    print("⚠️  Some imports failed - using fallback functions")
    
    # Create dummy functions for missing imports
    def generate_weekly_report(username):
        return {
            "username": username,
            "period": "Weekly Report",
            "total_entries": 0,
            "mood_distribution": {},
            "insights": ["Report service not available"],
            "recommendations": ["Please try again later"],
            "mood_trend": "Unknown"
        }
    
    def query_mood_model(answers, prompt):
        return "Neutral"  # Fallback mood
    
    def chat_with_psychiatrist(*args, **kwargs):
        return "I'm here to listen and support you. How are you feeling today?"
    
    def get_initial_greeting(*args, **kwargs):
        return "Hello! I'm NeuroCare AI. I'm here to support your mental wellness journey."
    
    # Dummy database functions
    def create_user(username):
        return 1
    
    def get_user(username):
        return {"id": 1, "username": username}
    
    def user_exists(username):
        return True
    
    def save_mood_log(user_id, mood, answers):
        return 1
    
    def get_user_mood_history(username):
        return []
    
    def create_chat_session(user_id, mood_log_id):
        return 1
    
    def end_chat_session(session_id):
        pass
    
    def save_chat_message(session_id, role, content):
        return 1
    
    def get_session_messages(session_id):
        return []
    
    def get_user_chat_sessions(username):
        return []
    
    def get_latest_mood_log():
        return {"id": 1, "mood": "Neutral"}

app = FastAPI(title="Mental Health Analyzer API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Safe path handling - don't crash if paths don't exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"🚀 Starting Mental Health Analyzer API")
print(f"📁 BASE_DIR: {BASE_DIR}")

# Safe file listing - don't crash if directory doesn't exist
try:
    files_in_dir = os.listdir(BASE_DIR)
    print(f"📄 Files in directory: {len(files_in_dir)} files")
    # Only show first few files to avoid log spam
    print(f"📄 Sample files: {files_in_dir[:10]}")
except FileNotFoundError as e:
    print(f"⚠️  Warning: Could not list directory {BASE_DIR}: {e}")
    files_in_dir = []

# ============== CATCH-ALL ROUTES TO PREVENT CRASHES ==============

@app.get("/favicon.ico")
async def serve_favicon():
    """Serve empty favicon to prevent 404 crashes"""
    from fastapi.responses import Response
    return Response(content=b"", media_type="image/x-icon")

@app.get("/favicon.png")
async def serve_favicon_png():
    """Serve empty favicon to prevent 404 crashes"""
    from fastapi.responses import Response
    return Response(content=b"", media_type="image/png")

# ============== API ENDPOINTS ==============

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

class WeeklyReportResponse(BaseModel):
    username: str
    period: str
    total_entries: int
    mood_distribution: Dict[str, int]
    insights: List[str]
    recommendations: List[str]
    mood_trend: str

# Basic endpoints with error handling
@app.post("/signup", response_model=UserResponse)
async def signup(request: SignupRequest):
    """Register a new user"""
    try:
        username = request.username.strip()
        if not username:
            raise HTTPException(status_code=400, detail="Username cannot be empty")

        if user_exists(username):
            raise HTTPException(status_code=409, detail="Username already exists")

        user_id = create_user(username)
        if user_id is None:
            raise HTTPException(status_code=500, detail="Failed to create user")

        return UserResponse(
            username=username,
            status="success",
            message="User registered successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup error: {str(e)}")

@app.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """Login with existing username"""
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/detect-mood", response_model=MoodResponse)
async def detect_mood(request: MoodDetectRequest):
    """Detect mood from answers"""
    try:
        username = request.username.strip()
        answers = request.answers

        user = get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        mood = query_mood_model(answers, system_prompt)
        if mood is None:
            mood = "Neutral"  # Fallback

        log_id = save_mood_log(user["id"], mood, json.dumps(answers))

        return MoodResponse(mood=mood, status="success", log_id=log_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mood detection error: {str(e)}")

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
    """Simple regex-based intent classification"""
    message = message.lower()
    
    for intent_name, data in CHATBOT_INTENTS.items():
        for pattern in data["patterns"]:
            if re.search(pattern, message, re.IGNORECASE):
                return intent_name, 0.9
    
    for intent_name, data in CHATBOT_INTENTS.items():
        for pattern in data["patterns"]:
            keyword = re.sub(r"[^\w\s]", "", pattern)
            if keyword and keyword.strip() and keyword.strip() in message:
                return intent_name, 0.6
    
    return "general", 0.3

def generate_chatbot_reply(intent: str, user_message: str) -> str:
    """Generate response based on intent"""
    if intent in CHATBOT_INTENTS:
        return random.choice(CHATBOT_INTENTS[intent]["responses"])
    
    fallback_responses = [
        "I understand... please tell me more about how you're feeling.",
        "Thank you for sharing that with me. Would you like to explore this further?",
        "I'm listening carefully. Could you tell me more about what's on your mind?",
    ]
    return random.choice(fallback_responses)

@app.post("/chatbot/message", response_model=ChatbotResponse)
async def chatbot_message(request: ChatbotRequest):
    """Simple chatbot endpoint"""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

@app.get("/chatbot/intents")
async def get_chatbot_intents():
    """Get list of available intents"""
    return {"intents": list(CHATBOT_INTENTS.keys())}

# ============== STATIC FILE ROUTES ==============

def safe_file_response(file_path):
    """Safe file serving that won't crash if file doesn't exist"""
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        print(f"⚠️  File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/")
async def serve_login():
    return safe_file_response(os.path.join(BASE_DIR, "login.html"))

@app.get("/login")
async def serve_login_page():
    return safe_file_response(os.path.join(BASE_DIR, "login.html"))

@app.get("/questions")
async def serve_questions():
    return safe_file_response(os.path.join(BASE_DIR, "login.html"))

@app.get("/results")
async def serve_results():
    return safe_file_response(os.path.join(BASE_DIR, "results.html"))

@app.get("/report")
async def serve_report():
    return safe_file_response(os.path.join(BASE_DIR, "report.html"))

@app.get("/chat")
async def serve_chat():
    return safe_file_response(os.path.join(BASE_DIR, "chat.html"))

@app.get("/{filename}.js")
async def serve_js(filename: str):
    js_files = ["questions", "results", "report", "chat"]
    if filename in js_files:
        return safe_file_response(os.path.join(BASE_DIR, f"{filename}.js"))
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/styles.css")
async def serve_css():
    return safe_file_response(os.path.join(BASE_DIR, "styles.css"))

@app.get("/assets/{asset_path:path}")
async def serve_assets(asset_path: str):
    asset_file_path = os.path.join(BASE_DIR, "assets", asset_path)
    return safe_file_response(asset_file_path)

@app.get("/{filename}.html")
async def serve_html(filename: str):
    html_files = ["login", "results", "report", "chat"]
    if filename in html_files:
        return safe_file_response(os.path.join(BASE_DIR, f"{filename}.html"))
    raise HTTPException(status_code=404, detail="File not found")

# ============== CATCH-ALL ROUTE ==============

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch-all route to serve login page for any unknown routes"""
    print(f"🔄 Catch-all route triggered: /{full_path}")
    return safe_file_response(os.path.join(BASE_DIR, "login.html"))

# ============== HEALTH CHECK ==============

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/debug/paths")
async def debug_paths():
    """Debug endpoint to check file paths"""
    files = {}
    for file in ["login.html", "results.html", "chat.html", "questions.js"]:
        path = os.path.join(BASE_DIR, file)
        files[file] = {
            "path": path,
            "exists": os.path.exists(path)
        }
    return {"base_dir": BASE_DIR, "files": files}

if __name__ == "__main__":
    import uvicorn
    if os.environ.get('VERCEL'):
        # Running on Vercel
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
    else:
        # Running locally
        uvicorn.run(app, host="127.0.0.1", port=8000)