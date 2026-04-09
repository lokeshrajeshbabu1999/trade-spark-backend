from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🔴 IMPORTANT: This expects you to have PostgreSQL installed on your computer.
# It expects a database user 'postgres' with password 'password', 
# and a database named 'tradespark'. 
# You can change these credentials to match your local setup.
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345@localhost:5432/tradespark"

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
