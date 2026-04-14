from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    conversation_messages = relationship("ConversationMessage", back_populates="user", cascade="all, delete-orphan")