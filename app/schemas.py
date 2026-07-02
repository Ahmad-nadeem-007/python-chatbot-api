# Pydantic models (API request/response validation)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Request schemas (User input)
class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

class MessageSend(BaseModel):
    chat_id: Optional[str] = None  # Agar Null hua to naya chat session backend khud banayega
    message: str

# Response schemas (API output)
class MessageResponse(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

# Pagination wrapper
class PaginatedMessages(BaseModel):
    chat_id: str
    total_messages: int
    page: int
    limit: int
    messages: List[MessageResponse]