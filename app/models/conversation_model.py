from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base


class ConversationMessage(Base):
    """Modelo para almacenar el historial de conversación entre el usuario y el chatbot."""
    
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String)  # "user" o "assistant"
    content = Column(Text)  # Contenido del mensaje
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relación con User
    user = relationship("User", back_populates="conversation_messages")
