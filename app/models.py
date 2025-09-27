import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship


from .database import Base


class User(Base):
   
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)


class Post(Base):
  
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    content_description = Column(String, nullable=True)

   
    category = Column(String, default='general')


class Interaction(Base):
    """
    Represents the 'interactions' table in the database.
    This is a linking table that records every time a user
    interacts with a post (e.g., a 'like' or a 'swipe').
    """
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    interaction_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    post = relationship("Post")

