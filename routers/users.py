from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import Users
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import CreateUserRequest, Token 
from datetime import timedelta


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
bycrpt_context = auth_services.bcrypt_context
authenticate_user = auth_services.authenticate_user

# signup
@router.post("/signup",status_code=status.HTTP_201_CREATED)
async def create_user(user: CreateUserRequest, db: db_dependency):
    user_model = Users(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        password=bycrpt_context.hash(user.password),
        role=user.role
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model

# login
@router.post("/login",response_model=Token)
async def login_for_access_token(db:db_dependency,form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password")
    access_token_expires = auth_services.timedelta(minutes=30)
    access_token = auth_services.create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


