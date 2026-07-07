from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DocumentSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    document_type: Optional[str] = Field(None, max_length=50)
    initiator: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=50)
    year: Optional[str] = Field(None, max_length=50)
    about: Optional[str] = None
    place_of_determination: Optional[str] = Field(None, max_length=255)
    date_of_determination: Optional[datetime] = None
    official: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    category_document: str = Field(..., min_length=1)
