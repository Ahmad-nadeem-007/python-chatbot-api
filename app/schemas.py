# Pydantic models (API request/response validation)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Request schemas (User input)
class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

class MessageSend(BaseModel):
    chat_id: Optional[str] = None  # If Null, the backend will create a new chat session automatically
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

# RAG / Knowledge Base schemas
class IngestResponse(BaseModel):
    status: str
    files_processed: int
    chunks_created: int

class SearchResult(BaseModel):
    content: str
    source: str
    distance: Optional[float] = None  # match score (lower = better)

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]