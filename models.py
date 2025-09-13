from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text
from datetime import datetime, timezone


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True, index=True)
    fullname = Column(String,index=True)
    username = Column(String,unique=True,index=True)
    email = Column(String,unique=True,index=True)
    password = Column(String,index=True)
    role = Column(String,index=True)
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))

# Model for posts
class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer,primary_key=True, index=True)
    title = Column(String,index=True)
    image = Column(LargeBinary,nullable=True) # Storing image as binary data
    content = Column(Text,index=True)
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    updated_at = Column(DateTime,index=True,default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    author_id = Column(Integer, ForeignKey("users.id"))

# Model for comments
class Comments(Base):
    __tablename__ = "comments"

    id = Column(Integer,primary_key=True,index=True)
    content = Column(Text,index=True)
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    post_id = Column(Integer, ForeignKey("posts.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True) # Self-referential foreign key for nested comments


