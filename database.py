from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import urllib.parse
import os 
from dotenv import load_dotenv

load_dotenv()

DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
SUPABASE_URL = os.getenv("SUPABASE_URL")
encoded_password = urllib.parse.quote_plus(str(DATABASE_PASSWORD))


POSTGRES_DATABASE_URL = (
     f"{DATABASE_USERNAME}:{encoded_password}"
     f"{SUPABASE_URL}:5432/postgres"
)
engine = create_engine(POSTGRES_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()