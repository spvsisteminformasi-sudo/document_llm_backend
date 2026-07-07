from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=6)
    role: str = Field(..., min_length=3, max_length=80)
    phone: str = Field(..., min_length=3, max_length=80)
