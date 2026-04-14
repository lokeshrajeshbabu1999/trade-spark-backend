import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔴 IMPORTANT: In local development, this expects PostgreSQL or falls back to SQLite.
# In production (AWS), this will be provided by an environment variable.
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./test.db"
)

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"⚠️ DATABASE WARNING: Failed to connect to PostgreSQL. Is it running? {e}")
    engine = None
    SessionLocal = None
    Base = None

def get_db():
    if not SessionLocal:
        raise Exception("Database is not connected. Ensure PostgreSQL is running.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
