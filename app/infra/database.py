from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

database = create_engine(DATABASE_URL)

def init_db():
    with Session(database) as session:
        yield session

class Base(DeclarativeBase):
    pass