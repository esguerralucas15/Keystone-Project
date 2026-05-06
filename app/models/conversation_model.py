from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base


class ConversationSession(Base):
    """Modelo para agrupar mensajes en sesiones de chat."""

    __tablename__ = "conversation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship("User", back_populates="conversation_sessions")
    messages = relationship(
        "ConversationMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    """Modelo para almacenar el historial de conversación entre el usuario y el chatbot."""
    
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(Integer, ForeignKey("conversation_sessions.id"), index=True)
    role = Column(String)  # "user" o "assistant"
    content = Column(Text)  # Contenido del mensaje
    created_at = Column(DateTime, default=datetime.now, index=True)

    # Relación con User
    user = relationship("User", back_populates="conversation_messages")
    session = relationship("ConversationSession", back_populates="messages")
