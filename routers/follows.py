from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from models import Users, Follows
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import PostBase, Postupdate
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError


router = APIRouter(
    prefix="/follows",
    tags=["follows"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth_services.get_current_user)]

# api to follow a user
@router.post("/follow/{user_id}", status_code=status.HTTP_200_OK)
async def follow_user(user_id:int, user: user_dependency, db: db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        follow_id = user["id"]
        if follow_id == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself.")
        user_to_follow = db.query(Users).filter(Users.id == user_id).first()
        if not user_to_follow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to follow not found.")
        new_follow  = Follows(follower_id=follow_id, following_id=user_id)
        db.add(new_follow)
        db.commit()
        db.refresh(new_follow)
        return {"message": "Followed successfully", "follow": new_follow}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already following this user.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# unfollow a user
@router.delete("/unfollow/{user_id}", status_code=status.HTTP_200_OK)
async def unfollow_user(user_id:int,db:db_dependency,user:user_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        unfollow_ud = user["id"]
        if unfollow_ud == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot unfollow yourself.")
        # Check if the user to be unfollowed exists
        user_to_infollow = db.query(Users).filter(Users.id == user_id).first()
        if not user_to_infollow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to unfollow not found.")
        # Check if the follow relationship exists
        follow_relationship  = db.query(Follows).filter(Follows.follower_id == unfollow_ud, Follows.following_id == user_id).first()
        if not follow_relationship:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are not following this user.")
        db.delete(follow_relationship)
        db.commit()
        return {"message": "Unfollowed successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# api to get followers of current user
@router.get("/followers", status_code=status.HTTP_200_OK)
async def get_followers(db:db_dependency,user:user_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        user_id = user["id"]
        followers = db.query(Follows).filter(Follows.follower_id == user_id).all()
        followers_username = []
        for follower in followers:
            user_model = db.query(Users).filter(Users.id == follower.following_id).first()
            if user_model:
                followers_username.append({
                    "id": user_model.id,
                    "username": user_model.username
                })
        return {"followers": followers_username}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))