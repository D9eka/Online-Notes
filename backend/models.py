import pytz
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.base import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    notes = relationship("Note", back_populates="owner")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC),
                        onupdate=lambda: datetime.now(pytz.UTC))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="notes")
    files = relationship("File", back_populates="note", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    note = relationship("Note", back_populates="files")

