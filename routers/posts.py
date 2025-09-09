from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from models import Users, Posts
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import PostBase
from datetime import timedelta
from sqlalchemy.exc import IntegrityError


router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth_services.get_current_user)]


# Get api for all posts
@router.get("/",status_code=status.HTTP_200_OK)
async def get_all_posts(user: user_dependency, db: db_dependency):
    try:
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        post_model = db.query(Posts).all()
        results = []
        for post in post_model:
            results.append({
                "title": post.title,
                "content": post.content,
                "image": f"/posts/{post.id}/image" if post.image else None,
                "created_at": post.created_at,
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# get api for image 
@router.get("/{post_id}/image")
async def get_post_image(post_id: int,user:user_dependency,db: db_dependency):
    post = db.query(Posts).filter(Posts.id == post_id).first()
    if not post or not post.image:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=post.image, media_type="image/jpeg")

# post api for creating a post
@router.post("/create_posts", status_code=status.HTTP_201_CREATED)
async def create_posts(
    user: user_dependency,
    db: db_dependency,
    posts: PostBase = Depends(PostBase.as_form),
    image: UploadFile | None = None
):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user_id = user.get("id")
    image_data = await image.read() if image else None

    post_model = Posts(
        title=posts.title,
        content=posts.content,
        image=image_data,
        author_id=user_id
    )

    db.add(post_model)
    db.commit()
    db.refresh(post_model)

    return {"message": "Post created successfully"}


        