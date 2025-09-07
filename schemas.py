from pydantic import BaseModel, Field, EmailStr


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