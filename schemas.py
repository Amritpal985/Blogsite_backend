from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from fastapi import Form


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=5)
    email: str
    password: str= Field(min_length=6)
    fullname: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    message: str
    username: str
    email: EmailStr

class PostBase(BaseModel):
    title: str
    content: str

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        content: str = Form(...)
    ):
        return cls(title=title, content=content)

class Postupdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=300)