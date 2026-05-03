from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_URL = "postgresql://admin:1234@localhost.postgres.db:5432/product_reviews?schema=public"

database = create_engine(DATABASE_URL)

def init_db():
    with Session(database) as session:
        yield session

class Base(DeclarativeBase):
    pass