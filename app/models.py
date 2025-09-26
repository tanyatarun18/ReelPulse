import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

# This is the base class that our models will inherit from.
# It's provided by SQLAlchemy to connect our classes to the database tables.
from .database import Base


class User(Base):
    """
    Represents the 'users' table in the database.
    Each row will be a unique user in our system.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)


class Post(Base):
    """
    Represents the 'posts' table in the database.
    Each row will be a unique video post.
    """
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True, nullable=False)
    content_description = Column(String, nullable=True)

    # --- THIS IS THE NEW, IMPORTANT COLUMN ---
    # This column will store the mood or category of the video,
    # for example: 'motivational', 'educational', etc.
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

    # These relationships help SQLAlchemy understand how the tables are connected.
    user = relationship("User")
    post = relationship("Post")

