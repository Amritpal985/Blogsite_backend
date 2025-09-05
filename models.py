from database import Base
from sqlalchemy import Column, Integer, String, DateTime
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
