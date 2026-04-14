from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.user_model import User
from app.models.profile_model import UserProfile
from app.llm.google_llm_new import procesar_mensaje_chatbot, generar_recomendacion_inicial

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/message")
def chatbot_message(payload: dict, db: Session = Depends(get_db)):
    """
    Endpoint para procesar mensajes del chatbot.
    Recibe { user_id, message } y devuelve respuesta del asesor financiero.
    
    Flujo:
    1. Validar user_id
    2. Obtener datos del usuario y perfil de BD
    3. Procesar mensaje con el módulo LLM
    4. Retornar respuesta
    """
    user_id = payload.get("user_id")
    message = payload.get("message", "").strip()

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    # Obtener usuario de BD
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Obtener perfil financiero
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    # Datos del usuario
    user_data = {"id": user.id, "name": user.name, "email": user.email}

    # Datos del perfil (si existen)
    profile_data = {}
    if profile:
        profile_data = {
            c.name: getattr(profile, c.name) 
            for c in profile.__table__.columns 
            if c.name not in ("id", "user_id")
        }

    try:
        # Procesar mensaje
        resultado = procesar_mensaje_chatbot(user_id, message, user_data, profile_data)
        
        if resultado.get("error"):
            raise HTTPException(status_code=400, detail=resultado["error"])
        
        return {
            "input": {
                "user": user_data,
                "profile": profile_data,
                "message": message
            },
            "reply": resultado.get("reply")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")


@router.post("/initial-recommendation")
def chatbot_initial_recommendation(payload: dict, db: Session = Depends(get_db)):
    """
    Endpoint para generar la recomendación inicial cuando el usuario entra al chatbot por primera vez.
    Recibe { user_id } y devuelve recomendación personalizada basada en su perfil.
    
    Flujo:
    1. Validar user_id
    2. Obtener datos del usuario y perfil de BD
    3. Generar recomendación inicial con IA
    4. Retornar recomendación
    """
    user_id = payload.get("user_id")

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    # Obtener usuario de BD
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Obtener perfil financiero
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil financiero no encontrado. Por favor completa la encuesta de onboarding.")

    # Datos del usuario
    user_data = {"id": user.id, "name": user.name, "email": user.email}

    # Datos del perfil
    profile_data = {
        c.name: getattr(profile, c.name) 
        for c in profile.__table__.columns 
        if c.name not in ("id", "user_id")
    }

    try:
        # Generar recomendación inicial
        recomendacion = generar_recomendacion_inicial(profile_data, user_data)
        
        return {
            "user": user_data,
            "recommendation": recomendacion
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendación: {str(e)}")


@router.get("/debug")
def chatbot_debug():
    """Endpoint de debug para verificar estado del chatbot."""
    import sys
    info = {
        "sys_executable": sys.executable,
        "status": "ok",
        "chatbot_available": True
    }
    return info
