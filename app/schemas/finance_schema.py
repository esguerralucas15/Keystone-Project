from typing import Optional
from pydantic import BaseModel


class FinanceProfileUpsert(BaseModel):
    user_id: int
    monthly_income: float


class DailyRecordCreate(BaseModel):
    user_id: int
    record_date: Optional[str] = None
    expenses: float
    expense_type: str
    category: str
    note: Optional[str] = None


class SavingsGoalCreate(BaseModel):
    user_id: int
    title: str
    target_amount: float
    target_months: int


class SavingsCheckinCreate(BaseModel):
    record_date: Optional[str] = None
    saved_amount: float
