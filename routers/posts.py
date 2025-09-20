from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from models import Users, Posts
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import PostBase, Postupdate
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from models import TagsEnum

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

# Get api for all posts along with its authorname and userid
@router.get("/",status_code=status.HTTP_200_OK)
async def get_all_posts_partial(db: db_dependency):
    try:
        # query to fetch all posts with its userid and username
        post_model = db.query(Posts).join(Users, Posts.author_id == Users.id).with_entities(
            Posts.id,
            Posts.title,
            Posts.tag,
            Posts.content,
            Posts.created_at,
            Users.id.label("author_id"),
            Users.username.label("author_username")
        ).all()
        result = []
        for post in post_model:
            content = post.content[:70] + "..." if len(post.content) > 70 else post.content
            result.append({
                "id": post.id,
                "title": post.title,
                "content": content,
                "tag": post.tag,
                "created_at": post.created_at,
                "author": {
                    "id": post.author_id,
                    "username": post.author_username
                }
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# get api to all info for a particular post
@router.get("/{post_id}",status_code=status.HTTP_200_OK)
async def get_post_detail(post_id:int,user:user_dependency,db: db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        post_model = db.query(Posts).filter(Posts.id == post_id).first()
        if not post_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        res = []
        res.append({
            "id": post_model.id,
            "title": post_model.title,
            "content": post_model.content,
            "tag": [tag for tag in post_model.tag],
            "image": f"/posts/{post_id}/image" if post_model.image else None,
            "created_at": post_model.created_at,
            "updated_at": post_model.updated_at,
            "author_id": post_model.author_id
        })
        return res
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
        tag=[t.value for t in posts.tag], # Convert enum to string values
        image=image_data,
        author_id=user_id
    )

    db.add(post_model)
    db.commit()
    db.refresh(post_model)

    return {"message": "Post created successfully"}

# put api for updating a post
@router.put("/{post_id}/update", status_code=status.HTTP_200_OK)
async def updated_post(
    post_id:int,
    user: user_dependency,
    db: db_dependency,
    posts: Postupdate = Depends(Postupdate),
    image: UploadFile | None = File(None)
):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        post_model = db.query(Posts).filter(Posts.id == post_id).first()
        if not post_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")
        if post_model.author_id != user.get("id"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this post")
        if posts.title is not None:
            post_model.title = posts.title
        if posts.content is not None:
            post_model.content = posts.content
        post_model.updated_at = datetime.now(timezone.utc)
        if image is not None:
            image_data = await image.read()
            post_model.image = image_data
        db.commit()
        db.refresh(post_model)
        return {"message": "Post updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# api to add more tags for a particular posts
@router.put("/{post_id}/add_tags", status_code=status.HTTP_200_OK)
async def add_tags_to_post(
    post_id:int,
    user: user_dependency,
    db: db_dependency,
    tags: list[TagsEnum]
):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        post_model = db.query(Posts).filter(Posts.id == post_id).first()
        if not post_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")
        if post_model.author_id != user.get("id"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this post")
        
        # Add new tags, avoiding duplicates
        existing_tags = set(post_model.tag)
        new_tags = set(t.value for t in tags)  # Convert enum to string values
        updated_tags = list(existing_tags.union(new_tags))
        post_model.tag = updated_tags

        post_model.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(post_model)
        return {"message": "Tags added successfully", "tags": post_model.tag}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


        