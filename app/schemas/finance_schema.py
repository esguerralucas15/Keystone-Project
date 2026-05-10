from typing import Optional
from pydantic import BaseModel


class FinanceRecordCreate(BaseModel):
    user_id: int
    record_date: Optional[str] = None
    income: float
    fixed_expenses: float
    variable_expenses: float
    debt_payment: float
    savings_current: Optional[float] = None
    goal_amount: Optional[float] = None
