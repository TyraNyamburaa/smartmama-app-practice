import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

LOCAL_DATABASE_URL = (
    "postgresql://postgres:postgres@localhost:5432/smartmama_db"
)

database_url = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL)


if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )


engine = create_engine(
    database_url,
    pool_pre_ping=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()