from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.user_model import User
from app.models.profile_model import UserProfile
from app.llm.google_llm import generate_reply

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/message")
def chatbot_message(payload: dict, db: Session = Depends(get_db)):
    """Recibe { user_id, message } y devuelve los datos del usuario + respuesta del LLM."""
    user_id = payload.get("user_id")
    message = payload.get("message", "")

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    user_data = {"id": user.id, "name": user.name, "email": user.email}

    profile_data = {}
    if profile:
        profile_data = {c.name: getattr(profile, c.name) for c in profile.__table__.columns if c.name not in ("id", "user_id")}

    try:
        reply = generate_reply(user_data, profile_data, message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"input": {"user": user_data, "profile": profile_data, "message": message}, "reply": reply}


@router.get('/debug')
def chatbot_debug():
    import sys, importlib
    info = {"sys_executable": sys.executable}
    try:
        mod = importlib.import_module('app.llm.google_llm')
        info['google_llm_module'] = getattr(mod, '__file__', None)
        info['ChatGoogleGenerativeAI'] = str(getattr(mod, 'ChatGoogleGenerativeAI', None))
        info['_import_error'] = getattr(mod, '_import_error', None)
    except Exception as e:
        info['google_llm_module_error'] = str(e)

    try:
        import langchain_google_genai as lg
        info['langchain_google_genai'] = getattr(lg, '__file__', None)
    except Exception as e:
        info['langchain_google_genai_error'] = str(e)

    try:
        from langchain_core.messages import HumanMessage
        info['langchain_core_messages'] = 'ok'
    except Exception as e:
        info['langchain_core_messages_error'] = str(e)

    return info
