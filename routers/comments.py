from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from models import Users, Posts, Comments
from database import SessionLocal
from typing import Annotated
from services import auth_services
from schemas import CommentBase
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[Session,Depends(auth_services.get_current_user)]

# to get all comments for a Particular post
@router.get("/{post_id}",status_code=status.HTTP_200_OK)
async def get_comment_for_post(post_id:int,user:user_dependency,db:db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    try:
        comment_model = db.query(Comments).filter(Comments.post_id==post_id).all()
        # want in the format of list of dict comment_id, content, author_name, created_at, children
        # children is an array containing id, author of thet child comment, content and then again children
        if not comment_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No comments found for this post")
        def build_comment_tree(comments, parent_id=None):
            tree = []
            for comment in comments:
                print(comment.parent_comment_id, parent_id)
                if comment.parent_comment_id == parent_id:
                    author = db.query(Users).filter(Users.id == comment.author_id).first()
                    comment_dict = {
                        "id": comment.id,
                        "content": comment.content,
                        "author_name": author.fullname if author else "Unknown",
                        "created_at": comment.created_at,
                        "children": build_comment_tree(comments, comment.id)
                    }
                    tree.append(comment_dict)
            return tree
        comment_tree = build_comment_tree(comment_model)
        return comment_tree
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))

# To make a comment for a post
@router.post("/{post_id}",status_code=status.HTTP_201_CREATED)
async def post_comment(post_id:int,comment:CommentBase,user:user_dependency,db:db_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    try:
        post_exists = db.query(Posts).filter(Posts.id == post_id).first()
        if not post_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        user_id = user.get("id")
        comment_model = Comments(
            content = comment.content,
            post_id = post_id,
            author_id = user_id
        )
        db.add(comment_model)
        db.commit()
        db.refresh(comment_model)
        return {"message":"Comment Added"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))

# To make a nested comment
@router.post("/reply/{comment_id}",status_code=status.HTTP_201_CREATED)
async def post_nested_comment(comment_id:int,user:user_dependency,db:db_dependency,comment:CommentBase):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized")
    try:
        parent_comment = db.query(Comments).filter(Comments.id == comment_id).first()
        if not parent_comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")
        user_id = user.get("id")
        nested_comment = Comments(
            content = comment.content,
            post_id = parent_comment.post_id,
            author_id = user_id,
            parent_comment_id = comment_id
        )
        db.add(nested_comment)
        db.commit()
        db.refresh(nested_comment)
        return {"message":"Nested Comment Added"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=str(e))



