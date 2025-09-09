from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import urllib.parse
import os 

DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
encoded_password = urllib.parse.quote_plus(DATABASE_PASSWORD)


POSTGRES_DATABASE_URL = (
     f"postgresql+psycopg2://postgres.ushkvpjiylhrqyxghtrx:{encoded_password}"
     "@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
)
engine = create_engine(POSTGRES_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()