from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime, timezone
from enum import Enum


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True, index=True)
    fullname = Column(String,index=True)
    username = Column(String,unique=True,index=True)
    email = Column(String,unique=True,index=True)
    password = Column(String,index=True)
    role = Column(String,index=True)
    bio = Column(String, nullable=True)
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    image = Column(LargeBinary, nullable=True)   
    about_me = Column(Text, nullable=True)

# Model for posts
class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer,primary_key=True, index=True)
    title = Column(String,index=True)
    image = Column(LargeBinary,nullable=True) # Storing image as binary data
    content = Column(Text,index=True)
    tag = Column(String, default="Other") # to-do make it string of values
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    updated_at = Column(DateTime,index=True,default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    author_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))


# Model for comments
class Comments(Base):
    __tablename__ = "comments"

    id = Column(Integer,primary_key=True,index=True)
    content = Column(Text,index=True)
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    post_id = Column(Integer, ForeignKey("posts.id",ondelete="CASCADE"))
    author_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))
    parent_comment_id = Column(Integer, ForeignKey("comments.id",ondelete="CASCADE"), nullable=True) 
# model for likes
class Likes(Base):
    __tablename__ = "likes"

    id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey("posts.id",ondelete="CASCADE"))

# model for follows
class Follows(Base):
    __tablename__ = "follows"

    id = Column(Integer,primary_key=True,index=True)
    follower_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))
    following_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))

# model for chat messages
class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer,primary_key=True,index=True)
    sender_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))
    receiver_id = Column(Integer, ForeignKey("users.id",ondelete="CASCADE"))
    message = Column(Text,index=True)
    timestamp = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    is_read = Column(Integer, default=0)  # 0 for unread,

