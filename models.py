from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from .database import Base



class Post(Base):
    __tablename__ =  "posts"

    id = Column(Integer, primary_key=True, nullable=False,autoincrement=True)
    title = Column(String, nullable=False)
    content=Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))
