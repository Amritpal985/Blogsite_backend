from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
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
    content = Column(String,index=True)
    created_at = Column(DateTime,index=True,default=datetime.now(timezone.utc))
    updated_at = Column(DateTime,index=True,default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    author_id = Column(Integer, ForeignKey("users.id"))

# Model for comments

