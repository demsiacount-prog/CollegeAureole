import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Remplacez par vos identifiants PostgreSQL réels dans le fichier .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://demsi:malademsi15@localhost:5432/collegeaureole",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
