from pydantic import BaseModel, Field
from typing import Optional

class TagSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[int] = None
    document_id: Optional[int] = None
    page_number: Optional[int] = None
    tag_type: str = Field(..., min_length=1, max_length=50)
