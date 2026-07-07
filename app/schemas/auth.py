from pydantic import BaseModel, Field, EmailStr

class RegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6)
    phone: str = Field(..., min_length=4, max_length=15)
