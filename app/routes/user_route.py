from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate
from app.models.user_model import User
from app.database.database import SessionLocal
from app.schemas.user_schema import UserLogin
from app.schemas.profile_schema import ProfileSchema
from app.utils.security import verify_password_with_db  # Cambiamos la importación

router = APIRouter()

# conexión a DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Usuario creado",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "has_profile": False
        }
    }


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    return {
        "message": "Login exitoso ✅",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "has_profile": db_user.profile is not None
        }
    }


from app.models.profile_model import UserProfile


@router.post("/onboarding/{user_id}")
def save_profile(user_id: int, profile: ProfileSchema, db: Session = Depends(get_db)):

    new_profile = UserProfile(
        user_id=user_id,
        q1=profile.q1,
        q2=profile.q2,
        q3=profile.q3,
        q4=profile.q4,
        q5=profile.q5,
        q6=profile.q6,
        q7=profile.q7,
        q8=profile.q8,
        q9=profile.q9,
        q10=profile.q10,
        q11=profile.q11,
        q12=profile.q12,
        q13=profile.q13,
        q14=profile.q14,
        q15=profile.q15,
        q16=profile.q16
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return {"message": "Perfil guardado"}


@router.delete("/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(user)
    db.commit()

    return {"message": "Usuario eliminado correctamente 🗑️"}