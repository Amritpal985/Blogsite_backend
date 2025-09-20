from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import Users
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import CreateUserRequest, Token, UserResponse
from datetime import timedelta
from sqlalchemy.exc import IntegrityError


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
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: CreateUserRequest, 
    db: Session = Depends(get_db)
):
    # check if username or email already exists
    existing_user = db.query(Users).filter(
        (Users.username == user.username) | (Users.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered."
        )
    
    # create user object
    user_model = Users(
        fullname=user.fullname,
        username=user.username,
        email=user.email,
        password=bycrpt_context.hash(user.password),
        role=user.role
    )

    try:
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred."
        )

    return UserResponse(
        message=f"User '{user_model.username}' created successfully.",
        username=user_model.username,
        email=user_model.email
    )

# login
@router.post("/login",response_model=Token)
async def login_for_access_token(db:db_dependency,form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password")
    access_token = auth_services.create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# api to get current user info
@router.get("/me",status_code=status.HTTP_200_OK)
async def read_users_me(current_user: Annotated[dict, Depends(auth_services.get_current_user)]):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        user = {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "email": current_user.get("email"),
            "role": current_user.get("role")
        }
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


