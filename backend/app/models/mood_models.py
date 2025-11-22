from pydantic import BaseModel
from typing import Optional, List, Dict

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

class WeeklyReportResponse(BaseModel):
    username: str
    period: str
    total_entries: int
    mood_distribution: Dict[str, int]
    insights: List[str]
    recommendations: List[str]
    mood_trend: str