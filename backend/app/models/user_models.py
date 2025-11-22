from pydantic import BaseModel
from typing import Optional, Dict, List

class SignupRequest(BaseModel):
    username: str

class LoginRequest(BaseModel):
    username: str

class UserResponse(BaseModel):
    username: str
    status: str
    message: str

class MoodDetectRequest(BaseModel):
    username: str
    answers: Dict[str, str]

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