from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    links = relationship("Link", back_populates="owner")

class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True, nullable=False)
    original_url = Column(String, nullable=False)
    custom_alias = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="links")

class ExpiredLink(Base):
    __tablename__ = "expired_links"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, index=True)
    original_url = Column(String)
    created_at = Column(DateTime)
    expired_at = Column(DateTime, default=datetime.utcnow)
    total_accesses = Column(Integer)
    user_id = Column(Integer, nullable=True)
