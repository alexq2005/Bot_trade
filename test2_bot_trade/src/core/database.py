from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import settings

# Use SQLite for simplicity and portability
DATABASE_URL = "sqlite:///./trading_bot.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # Needed for SQLite

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates all tables in the database."""
    Base.metadata.create_all(bind=engine)
