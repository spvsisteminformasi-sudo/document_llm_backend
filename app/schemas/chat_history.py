from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class ChatHistorySchema(BaseModel):
    id: Optional[int] = None
    chat_session_id: int = Field(..., description="ID of the chat session")
    query: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    sources: Optional[Dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
