from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database.database import Base


class FinanceProfile(Base):
    __tablename__ = "finance_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    monthly_income = Column(Float)
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, index=True)

    user = relationship("User", back_populates="finance_profile")


class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    record_date = Column(Date, default=date.today, index=True)
    expenses = Column(Float)
    expense_type = Column(String)
    category = Column(String)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship("User", back_populates="daily_records")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String)
    target_amount = Column(Float)
    target_months = Column(Integer)
    start_date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.now, index=True)

    user = relationship("User", back_populates="savings_goals")
    checkins = relationship(
        "SavingsCheckin",
        back_populates="goal",
        cascade="all, delete-orphan",
    )


class SavingsCheckin(Base):
    __tablename__ = "savings_checkins"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("savings_goals.id"), index=True)
    record_date = Column(Date, default=date.today, index=True)
    saved_amount = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now, index=True)

    goal = relationship("SavingsGoal", back_populates="checkins")
