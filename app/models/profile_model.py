from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class UserProfile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    q1 = Column(String)
    q2 = Column(String)
    q3 = Column(String)
    q4 = Column(String)
    q5 = Column(String)
    q6 = Column(String)
    q7 = Column(String)
    q8 = Column(String)
    q9 = Column(String)
    q10 = Column(String)
    q11 = Column(String)
    q12 = Column(String)
    q13 = Column(String)
    q14 = Column(String)
    q15 = Column(String)
    q16 = Column(String)
    q17 = Column(String)

    # 🔗 relación inversa (CLAVE)
    user = relationship("User", back_populates="profile")