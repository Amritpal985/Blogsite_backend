from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from models import Users, Posts, Likes
from database import SessionLocal
from typing import Annotated
from services import auth_services
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/likes",
    tags=["likes"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth_services.get_current_user)]

# get api to all likes for a particular post
@router.get("/{post_id}",status_code=status.HTTP_200_OK)
async def get_likes_for_post(post_id:int,db: db_dependency):
    try:
        likes = db.query(Likes).filter(Likes.post_id == post_id).all()
        return {"post_id": post_id, "likes_count": len(likes), "likes": [{"id": like.id, "user_id": like.user_id} for like in likes]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# post id to like a post
@router.post("/{post_id}",status_code=status.HTTP_201_CREATED)
async def like_post(post_id:int,user:user_dependency,db: db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        new_like = Likes(user_id=user["id"], post_id=post_id)
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return {"message": "Post liked successfully", "like": {"id": new_like.id, "user_id": new_like.user_id, "post_id": new_like.post_id}}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already liked this post")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# delete api to unlike a post
@router.delete("/{post_id}",status_code=status.HTTP_200_OK)
async def unlike_post(post_id:int,user:user_dependency,db: db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        like = db.query(Likes).filter(Likes.post_id == post_id, Likes.user_id == user["id"]).first()
        if not like:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found")
        db.delete(like)
        db.commit()
        return {"message": "Post unliked successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
