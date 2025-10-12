from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlalchemy import or_
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from models import Users, Posts, Likes 
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import PostBase, Postupdate
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from fastapi import Form, File, UploadFile

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
# with pagination
@router.get("/",status_code=status.HTTP_200_OK)
def get_all_posts_partial(db: db_dependency,page_number: int = 1, page_size: int = 2):
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
        ).offset((page_number - 1) * page_size).limit(page_size).all()
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
def get_post_detail(post_id:int,db: db_dependency):
    try:
        post_model = db.query(Posts).filter(Posts.id == post_id).first()
        author_id = post_model.author_id if post_model else None
        like_count = db.query(Likes).filter(Likes.post_id == post_id).count()

        author_username = db.query(Users.username).filter(Users.id == author_id).first() if author_id else None
        if not post_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        res = []
        res.append({
            "id": post_model.id,
            "title": post_model.title,
            "content": post_model.content,
            "tags": post_model.tag,
            "image": f"/posts/{post_id}/image" if post_model.image else None,
            "created_at": post_model.created_at,
            "updated_at": post_model.updated_at,
            "like_count": like_count,
            "author": {
                "id": post_model.author_id,
                "username": author_username[0] if author_username else None
            }
        })
        # return as object
        return res[0] if res else None
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# get api(filter api) for posts by tag and author username(LIKE)
@router.get("/filter/{author}/{tag}",status_code=status.HTTP_200_OK)
def filter_posts(db: db_dependency,user:user_dependency,tag:str,author:str):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        query = db.query(Posts,Users.username).join(Users, Posts.author_id == Users.id)
        if tag.lower() != "all":
            tag_list = [tag.strip() for tag in tag.split(",") if tag.strip()]
            print(tag_list)
            tag_filters = [Posts.tag.ilike(f"%{t}%") for t in tag_list]
            query = query.filter(or_(*tag_filters))
        
        query = query.filter(Users.username.ilike(f"%{author}%"))

        records = query.all()
        result = []
        for post_model, author_username in records:
              content = (
                post_model.content[:70] + "..."
                if len(post_model.content) > 70
                else post_model.content
            )
              result.append({
                    "id": post_model.id,
                    "title": post_model.title,
                    "content": content,
                    "tag": post_model.tag,
                    "created_at": post_model.created_at,
                    "author": {
                        "id": post_model.author_id,
                        "username": author_username
                    }
                })
        return result
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
    title: str = Form(...),
    content: str = Form(...),
    tag: str = Form(...),  # comma-separated string, e.g. "Health,Culture"
    image: UploadFile | None = File(None)
):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user_id = user.get("id")
    image_data = await image.read() if image else None

    post_model = Posts(
        title=title,
        content=content,
        tag=",".join(tag.split(",")),  # store as simple string
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
    


        