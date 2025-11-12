from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from fastapi import Form, UploadFile, File


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class UserResponse(BaseModel):
    message: str
    username: str
    email: EmailStr

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    tag: Optional[str] = "Other"



class Postupdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=300)


class ChatRequest(BaseModel):
    receiver_id: int
    message: str

class UpdateUserForm:
    def __init__(
        self,
        fullname: Optional[str] = Form(None),
        username: Optional[str] = Form(None),
        password: Optional[str] = Form(None),
        about_me: Optional[str] = Form(None),
        image: Optional[UploadFile] = File(None)
    ):
        self.fullname = fullname
        self.username = username
        self.password = password
        self.about_me = about_me
        self.image = image
