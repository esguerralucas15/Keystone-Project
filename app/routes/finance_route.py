from datetime import datetime, date, timedelta
import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.user_model import User
from app.models.finance_model import FinanceRecord
from app.schemas.finance_schema import FinanceRecordCreate

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_record_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")


def _compute_score(monthly_income: float, fixed_expenses: float, variable_expenses: float, debt_payment: float):
    if monthly_income <= 0:
        return 0, "red"

    total_expenses = fixed_expenses + variable_expenses + debt_payment
    available = monthly_income - total_expenses

    savings_rate = max(available, 0) / monthly_income
    expense_ratio = (fixed_expenses + variable_expenses) / monthly_income
    debt_ratio = debt_payment / monthly_income

    if savings_rate >= 0.2:
        savings_score = 40
    elif savings_rate >= 0.1:
        savings_score = 30
    elif savings_rate >= 0.05:
        savings_score = 20
    elif savings_rate >= 0:
        savings_score = 10
    else:
        savings_score = 0

    if expense_ratio <= 0.5:
        expense_score = 30
    elif expense_ratio <= 0.7:
        expense_score = 20
    elif expense_ratio <= 0.9:
        expense_score = 10
    else:
        expense_score = 0

    if debt_ratio <= 0.1:
        debt_score = 30
    elif debt_ratio <= 0.2:
        debt_score = 20
    elif debt_ratio <= 0.3:
        debt_score = 10
    else:
        debt_score = 0

    score = max(0, min(100, savings_score + expense_score + debt_score))

    if score >= 70:
        color = "green"
    elif score >= 40:
        color = "yellow"
    else:
        color = "red"

    return score, color


def _aggregate_records(records: list[FinanceRecord]):
    total_income = sum(r.income for r in records)
    total_fixed = sum(r.fixed_expenses for r in records)
    total_variable = sum(r.variable_expenses for r in records)
    total_debt = sum(r.debt_payment for r in records)

    min_date = min(r.record_date for r in records)
    max_date = max(r.record_date for r in records)
    days = (max_date - min_date).days + 1
    days = max(days, 1)
    factor = 30 / days

    monthly_income = total_income * factor
    monthly_fixed = total_fixed * factor
    monthly_variable = total_variable * factor
    monthly_debt = total_debt * factor

    last_record = max(records, key=lambda r: (r.record_date, r.created_at))

    return {
        "days": days,
        "monthly_income": monthly_income,
        "monthly_fixed": monthly_fixed,
        "monthly_variable": monthly_variable,
        "monthly_debt": monthly_debt,
        "last_record": last_record,
    }


@router.post("/record")
def create_record(payload: FinanceRecordCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    record = FinanceRecord(
        user_id=payload.user_id,
        record_date=_parse_record_date(payload.record_date),
        income=payload.income,
        fixed_expenses=payload.fixed_expenses,
        variable_expenses=payload.variable_expenses,
        debt_payment=payload.debt_payment,
        savings_current=payload.savings_current,
        goal_amount=payload.goal_amount,
        created_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Registro guardado",
        "record_id": record.id,
    }


@router.get("/summary")
def get_summary(user_id: int, days: int = 30, db: Session = Depends(get_db)):
    if days <= 0:
        days = 30

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    since_date = date.today() - timedelta(days=days - 1)
    records = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id,
        FinanceRecord.record_date >= since_date,
    ).order_by(FinanceRecord.record_date.asc()).all()

    if not records:
        return {
            "user_id": user_id,
            "has_records": False,
            "message": "Sin registros financieros",
        }

    agg = _aggregate_records(records)
    monthly_income = agg["monthly_income"]
    monthly_fixed = agg["monthly_fixed"]
    monthly_variable = agg["monthly_variable"]
    monthly_debt = agg["monthly_debt"]
    monthly_expenses = monthly_fixed + monthly_variable + monthly_debt
    savings_capacity = monthly_income - monthly_expenses

    recommended_saving = 0
    if savings_capacity > 0:
        recommended_saving = min(savings_capacity, monthly_income * 0.1)

    score, color = _compute_score(monthly_income, monthly_fixed, monthly_variable, monthly_debt)

    goal_amount = agg["last_record"].goal_amount or 0
    goal_months = None
    if goal_amount and recommended_saving > 0:
        goal_months = int(math.ceil(goal_amount / recommended_saving))

    return {
        "user_id": user_id,
        "has_records": True,
        "period_days": agg["days"],
        "monthly_income": monthly_income,
        "monthly_fixed": monthly_fixed,
        "monthly_variable": monthly_variable,
        "monthly_debt": monthly_debt,
        "monthly_expenses": monthly_expenses,
        "savings_capacity": savings_capacity,
        "recommended_saving": recommended_saving,
        "score": score,
        "score_color": color,
        "goal_amount": goal_amount,
        "goal_months": goal_months,
        "last_record_date": agg["last_record"].record_date.isoformat(),
    }


@router.get("/records")
def list_records(user_id: int, limit: int = 30, db: Session = Depends(get_db)):
    if limit <= 0:
        limit = 30

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    records = db.query(FinanceRecord).filter(
        FinanceRecord.user_id == user_id,
    ).order_by(FinanceRecord.record_date.desc()).limit(limit).all()

    return {
        "user_id": user_id,
        "records": [
            {
                "id": record.id,
                "record_date": record.record_date.isoformat(),
                "income": record.income,
                "fixed_expenses": record.fixed_expenses,
                "variable_expenses": record.variable_expenses,
                "debt_payment": record.debt_payment,
                "savings_current": record.savings_current,
                "goal_amount": record.goal_amount,
            }
            for record in records
        ],
    }
