from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatSessionSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
