"""Database configuration and session management."""
import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./purser.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Create all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get a database session."""
    return Session(engine)
