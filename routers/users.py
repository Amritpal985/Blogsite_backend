from fastapi import APIRouter, HTTPException, Depends, status,File, UploadFile, Form
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import Users, Posts,Follows
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import  Token, UserResponse, UpdateUserForm
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
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    fullname: str = Form(...),
    role: str = Form(...),
    about_me: Optional[str] = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    existing_user = db.query(Users).filter(
        (Users.username == username) | (Users.email == email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered."
        )

    image_bytes = await image.read() if image else None
    user_model = Users(
        fullname=fullname,
        username=username,
        email=email,
        password=bycrpt_context.hash(password),
        role=role,
        about_me=about_me,
        image=image_bytes
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
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

# api to get current user info
# username,email,role, id, followers, following, total_posts
@router.get("/me",status_code=status.HTTP_200_OK)
async def read_users_me(current_user: Annotated[dict, Depends(auth_services.get_current_user)],db: db_dependency):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        model = db.query(Posts).filter(Posts.author_id == current_user.get("id")).all()
        total_posts = len(model)
        followers = db.query(Follows).filter(Follows.following_id == current_user.get("id")).count()
        following = db.query(Follows).filter(Follows.follower_id == current_user.get("id")).count()
        email = db.query(Users).filter(Users.id == current_user.get("id")).first().email
        user = {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "email": email,
            "role": current_user.get("role"),
            "total_posts": total_posts,
            "followers": followers,
            "following": following
        }
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# update user info
@router.put("/update", status_code=status.HTTP_200_OK)
async def update_user_info(
    current_user: Annotated[dict, Depends(auth_services.get_current_user)],
    db: db_dependency,
    form_data: UpdateUserForm = Depends()
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized"
        )

    try:
        current_user_id = current_user.get("id")
        user_model = db.query(Users).filter(Users.id == current_user_id).first()
        if not user_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )

        # Update only provided fields
        if form_data.fullname:
            user_model.fullname = form_data.fullname
        if form_data.username:
            user_model.username = form_data.username
        if form_data.password:
            user_model.password = bycrpt_context.hash(form_data.password)
        if form_data.about_me:
            user_model.about_me = form_data.about_me
        if form_data.image:
            image_bytes = await form_data.image.read()
            user_model.image = image_bytes

        db.commit()
        db.refresh(user_model)

        return {"message": "User information updated successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
