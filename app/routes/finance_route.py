from datetime import datetime, date, timedelta
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import SessionLocal
from app.models.user_model import User
from app.models.profile_model import UserProfile
from app.models.finance_model import (
    FinanceProfile,
    DailyRecord,
    SavingsGoal,
    SavingsCheckin,
)
from app.schemas.finance_schema import (
    FinanceProfileUpsert,
    DailyRecordCreate,
    SavingsGoalCreate,
    SavingsCheckinCreate,
)

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


def _compute_score(monthly_income: float, fixed_expenses: float, variable_expenses: float):
    if monthly_income <= 0:
        return 0, "red"

    total_expenses = fixed_expenses + variable_expenses
    available = monthly_income - total_expenses

    savings_rate = max(available, 0) / monthly_income
    expense_ratio = (fixed_expenses + variable_expenses) / monthly_income
    if savings_rate >= 0.2:
        savings_score = 50
    elif savings_rate >= 0.1:
        savings_score = 40
    elif savings_rate >= 0.05:
        savings_score = 30
    elif savings_rate >= 0:
        savings_score = 20
    else:
        savings_score = 0

    if expense_ratio <= 0.5:
        expense_score = 50
    elif expense_ratio <= 0.7:
        expense_score = 40
    elif expense_ratio <= 0.9:
        expense_score = 20
    else:
        expense_score = 0

    score = max(0, min(100, savings_score + expense_score))

    if score >= 70:
        color = "green"
    elif score >= 40:
        color = "yellow"
    else:
        color = "red"

    return score, color


def _serialize_profile(profile: FinanceProfile):
    return {
        "monthly_income": profile.monthly_income,
    }


def _extract_income_hint(profile: UserProfile | None):
    if not profile or not profile.q16:
        return None

    digits = re.sub(r"[^0-9]", "", str(profile.q16))
    if not digits:
        return None
    try:
        return float(digits)
    except ValueError:
        return None


def _goal_progress(db: Session, goal: SavingsGoal):
    total_saved = db.query(
        func.coalesce(func.sum(SavingsCheckin.saved_amount), 0)
    ).filter(
        SavingsCheckin.goal_id == goal.id
    ).scalar() or 0

    progress = 0
    if goal.target_amount > 0:
        progress = min(100, (total_saved / goal.target_amount) * 100)

    remaining = max(goal.target_amount - total_saved, 0)
    target_days = max(goal.target_months * 30, 1)
    daily_target = goal.target_amount / target_days

    return {
        "total_saved": total_saved,
        "progress": progress,
        "remaining": remaining,
        "daily_target": daily_target,
    }


@router.get("/profile")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile = db.query(FinanceProfile).filter(FinanceProfile.user_id == user_id).first()
    if not profile:
        onboarding = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        suggested = _extract_income_hint(onboarding)
        if suggested:
            profile = FinanceProfile(
                user_id=user_id,
                monthly_income=suggested,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        else:
            return {
                "user_id": user_id,
                "has_profile": False,
                "suggested_income": None,
            }

    return {
        "user_id": user_id,
        "has_profile": True,
        "profile": _serialize_profile(profile),
    }


@router.post("/profile")
def upsert_profile(payload: FinanceProfileUpsert, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile = db.query(FinanceProfile).filter(FinanceProfile.user_id == payload.user_id).first()
    if profile:
        profile.monthly_income = payload.monthly_income
        profile.updated_at = datetime.now()
    else:
        profile = FinanceProfile(
            user_id=payload.user_id,
            monthly_income=payload.monthly_income,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(profile)

    db.commit()

    return {
        "message": "Datos base guardados",
        "profile": _serialize_profile(profile),
    }


@router.post("/daily")
def create_daily_record(payload: DailyRecordCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile = db.query(FinanceProfile).filter(FinanceProfile.user_id == payload.user_id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Completa tus datos base antes de registrar el dia")

    if not payload.category or not payload.category.strip():
        raise HTTPException(status_code=400, detail="Categoria requerida")

    expense_type = payload.expense_type.strip().lower()
    if expense_type not in ("fixed", "variable"):
        raise HTTPException(status_code=400, detail="Tipo de gasto invalido")

    record = DailyRecord(
        user_id=payload.user_id,
        record_date=_parse_record_date(payload.record_date),
        expenses=payload.expenses,
        expense_type=expense_type,
        category=payload.category.strip(),
        note=payload.note.strip() if payload.note else None,
        created_at=datetime.now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Registro diario guardado",
        "record_id": record.id,
    }


@router.get("/summary")
def get_summary(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile = db.query(FinanceProfile).filter(FinanceProfile.user_id == user_id).first()
    if not profile:
        return {
            "user_id": user_id,
            "has_profile": False,
            "message": "Sin datos base",
        }

    monthly_income = profile.monthly_income

    since_date = date.today() - timedelta(days=29)
    records = db.query(DailyRecord).filter(
        DailyRecord.user_id == user_id,
        DailyRecord.record_date >= since_date,
    ).all()

    monthly_fixed = sum(r.expenses for r in records if r.expense_type == "fixed")
    monthly_variable = sum(r.expenses for r in records if r.expense_type == "variable")
    monthly_expenses = monthly_fixed + monthly_variable
    savings_capacity = monthly_income - monthly_expenses

    recommended_saving = 0
    if savings_capacity > 0:
        recommended_saving = min(savings_capacity, monthly_income * 0.1)

    if not records:
        score, color = 100, "green"
        has_records = False
    else:
        score, color = _compute_score(monthly_income, monthly_fixed, monthly_variable)
        has_records = True

    latest_goal = db.query(SavingsGoal).filter(
        SavingsGoal.user_id == user_id
    ).order_by(SavingsGoal.created_at.desc()).first()

    goal_info = None
    if latest_goal:
        progress = _goal_progress(db, latest_goal)
        goal_info = {
            "id": latest_goal.id,
            "title": latest_goal.title,
            "target_amount": latest_goal.target_amount,
            "target_months": latest_goal.target_months,
            "total_saved": progress["total_saved"],
            "progress": progress["progress"],
            "remaining": progress["remaining"],
            "daily_target": progress["daily_target"],
        }

    return {
        "user_id": user_id,
        "has_profile": True,
        "has_records": has_records,
        "monthly_income": monthly_income,
        "monthly_fixed": monthly_fixed,
        "monthly_variable": monthly_variable,
        "monthly_expenses": monthly_expenses,
        "savings_capacity": savings_capacity,
        "recommended_saving": recommended_saving,
        "recommended_daily": recommended_saving / 30 if recommended_saving else 0,
        "score": score,
        "score_color": color,
        "goal": goal_info,
    }


@router.get("/daily")
def list_daily_records(user_id: int, limit: int = 30, db: Session = Depends(get_db)):
    if limit <= 0:
        limit = 30

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    records = db.query(DailyRecord).filter(
        DailyRecord.user_id == user_id,
    ).order_by(DailyRecord.record_date.desc()).limit(limit).all()

    return {
        "user_id": user_id,
        "records": [
            {
                "id": record.id,
                "record_date": record.record_date.isoformat(),
                "expenses": record.expenses,
                "expense_type": record.expense_type,
                "category": record.category,
                "note": record.note,
            }
            for record in records
        ],
    }


@router.post("/goals")
def create_goal(payload: SavingsGoalCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.target_months <= 0:
        raise HTTPException(status_code=400, detail="Meses inválidos")

    goal = SavingsGoal(
        user_id=payload.user_id,
        title=payload.title.strip() or "Meta de ahorro",
        target_amount=payload.target_amount,
        target_months=payload.target_months,
        start_date=date.today(),
        created_at=datetime.now(),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    progress = _goal_progress(db, goal)

    return {
        "message": "Meta creada",
        "goal": {
            "id": goal.id,
            "title": goal.title,
            "target_amount": goal.target_amount,
            "target_months": goal.target_months,
            "total_saved": progress["total_saved"],
            "progress": progress["progress"],
            "remaining": progress["remaining"],
            "daily_target": progress["daily_target"],
        },
    }


@router.get("/goals")
def list_goals(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    goals = db.query(SavingsGoal).filter(
        SavingsGoal.user_id == user_id
    ).order_by(SavingsGoal.created_at.desc()).all()

    serialized = []
    for goal in goals:
        progress = _goal_progress(db, goal)
        serialized.append({
            "id": goal.id,
            "title": goal.title,
            "target_amount": goal.target_amount,
            "target_months": goal.target_months,
            "total_saved": progress["total_saved"],
            "progress": progress["progress"],
            "remaining": progress["remaining"],
            "daily_target": progress["daily_target"],
        })

    return {"user_id": user_id, "goals": serialized}


@router.post("/goals/{goal_id}/checkin")
def create_checkin(goal_id: int, payload: SavingsCheckinCreate, db: Session = Depends(get_db)):
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Meta no encontrada")

    checkin = SavingsCheckin(
        goal_id=goal_id,
        record_date=_parse_record_date(payload.record_date),
        saved_amount=payload.saved_amount,
        created_at=datetime.now(),
    )
    db.add(checkin)
    db.commit()

    progress = _goal_progress(db, goal)

    return {
        "message": "Registro de ahorro guardado",
        "goal_id": goal_id,
        "total_saved": progress["total_saved"],
        "progress": progress["progress"],
        "remaining": progress["remaining"],
    }
