from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database.database import SessionLocal
from app.models.user_model import User
from app.models.profile_model import UserProfile
from app.models.conversation_model import ConversationMessage, ConversationSession
from app.llm.google_llm_new import procesar_mensaje_chatbot, generar_recomendacion_inicial
from datetime import datetime

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _serialize_message(message: ConversationMessage):
    return {
        "id": message.id,
        "session_id": message.session_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat()
    }


def _serialize_session(session: ConversationSession, message_count=0, last_message_at=None):
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "message_count": message_count,
        "last_message_at": last_message_at.isoformat() if last_message_at else None,
    }


def _create_session(db: Session, user_id: int, title: Optional[str] = None):
    etiqueta = title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    session = ConversationSession(
        user_id=user_id,
        title=etiqueta,
        created_at=datetime.now(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/message")
def chatbot_message(payload: dict, db: Session = Depends(get_db)):
    """
    Endpoint para procesar mensajes del chatbot.
    Recibe { user_id, message } y devuelve respuesta del asesor financiero.
    
    Flujo:
    1. Validar user_id
    2. Obtener datos del usuario y perfil de BD
    3. Recuperar historial de conversación anterior
    4. Procesar mensaje con el módulo LLM (considerando el historial)
    5. Guardar mensaje del usuario y respuesta en el historial
    6. Retornar respuesta
    """
    user_id = payload.get("user_id")
    message = payload.get("message", "").strip()

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    # Obtener usuario de BD
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    session_id = payload.get("session_id")

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
        # Obtener o crear sesion
        session = None
        if session_id:
            session = db.query(ConversationSession).filter(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id,
            ).first()
            if not session:
                raise HTTPException(status_code=404, detail="Sesion no encontrada")
        else:
            session = _create_session(db, user_id)

        # Recuperar historial previo (ultimas interacciones de la sesion)
        historial_previo = db.query(ConversationMessage).filter(
            ConversationMessage.user_id == user_id,
            ConversationMessage.session_id == session.id,
        ).order_by(ConversationMessage.created_at.desc()).limit(20).all()
        
        # Invertir para que esté en orden cronológico
        historial_previo.reverse()
        
        # Convertir a formato esperado
        historial_conversacion = [
            {"role": msg.role, "content": msg.content}
            for msg in historial_previo
        ]

        # Procesar mensaje
        resultado = procesar_mensaje_chatbot(user_id, message, user_data, profile_data, historial_conversacion)
        
        if resultado.get("error"):
            raise HTTPException(status_code=400, detail=resultado["error"])
        
        # Guardar mensaje del usuario en el historial
        msg_usuario = ConversationMessage(
            user_id=user_id,
            session_id=session.id,
            role="user",
            content=message,
            created_at=datetime.now()
        )
        db.add(msg_usuario)
        db.commit()
        
        # Guardar respuesta del asistente en el historial
        msg_asistente = ConversationMessage(
            user_id=user_id,
            session_id=session.id,
            role="assistant",
            content=resultado.get("reply"),
            created_at=datetime.now()
        )
        db.add(msg_asistente)
        db.commit()
        
        return {
            "session_id": session.id,
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


## NOTE: Old history endpoints removed in favor of session-based chat history.


@router.post("/initial-recommendation")
def chatbot_initial_recommendation(payload: dict, db: Session = Depends(get_db)):
    """
    Endpoint para generar la recomendación inicial cuando el usuario entra al chatbot por primera vez.
    Recibe { user_id } y devuelve recomendación personalizada basada en su perfil.
    
    Flujo:
    1. Validar user_id
    2. Obtener datos del usuario y perfil de BD
    3. Generar recomendación inicial con IA
    4. Guardar recomendación en el historial
    5. Retornar recomendación
    """
    user_id = payload.get("user_id")

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    # Obtener usuario de BD
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    session_id = payload.get("session_id")

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
        # Obtener o crear sesion
        session = None
        if session_id:
            session = db.query(ConversationSession).filter(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id,
            ).first()
            if not session:
                raise HTTPException(status_code=404, detail="Sesion no encontrada")
        else:
            session = _create_session(db, user_id, title="Chat inicial")

        # Generar recomendacion inicial
        recomendacion = generar_recomendacion_inicial(profile_data, user_data)

        follow_up = (
            "Si quieres, puedes preguntarme sobre ahorro, presupuesto, credito o metas."
        )
        
        # Guardar recomendación en el historial de conversación
        msg_recomendacion = ConversationMessage(
            user_id=user_id,
            session_id=session.id,
            role="assistant",
            content=recomendacion,
            created_at=datetime.now()
        )
        db.add(msg_recomendacion)
        db.commit()

        msg_follow_up = ConversationMessage(
            user_id=user_id,
            session_id=session.id,
            role="assistant",
            content=follow_up,
            created_at=datetime.now()
        )
        db.add(msg_follow_up)
        db.commit()
        
        return {
            "user": user_data,
            "session_id": session.id,
            "recommendation": recomendacion,
            "follow_up": follow_up,
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


@router.post("/session")
def chatbot_create_session(payload: dict, db: Session = Depends(get_db)):
    user_id = payload.get("user_id")
    title = payload.get("title")

    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    session = _create_session(db, user_id, title=title)
    return {"session": _serialize_session(session)}


@router.get("/sessions")
def chatbot_sessions(user_id: int, db: Session = Depends(get_db)):
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    rows = db.query(
        ConversationSession,
        func.count(ConversationMessage.id).label("count"),
        func.max(ConversationMessage.created_at).label("last_message_at"),
    ).outerjoin(
        ConversationMessage,
        ConversationMessage.session_id == ConversationSession.id,
    ).filter(
        ConversationSession.user_id == user_id
    ).group_by(ConversationSession.id).order_by(ConversationSession.created_at.desc()).all()

    sessions = [
        _serialize_session(row[0], row[1], row[2])
        for row in rows
    ]

    return {"user_id": user_id, "sessions": sessions}


@router.get("/history")
def chatbot_history(
    user_id: int,
    session_id: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es requerido")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if limit <= 0:
        limit = 20

    if session_id:
        session = db.query(ConversationSession).filter(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Sesion no encontrada")
    else:
        session = db.query(ConversationSession).filter(
            ConversationSession.user_id == user_id,
        ).order_by(ConversationSession.created_at.desc()).first()

    if not session:
        return {"user_id": user_id, "session_id": None, "messages": []}

    mensajes = db.query(ConversationMessage).filter(
        ConversationMessage.user_id == user_id,
        ConversationMessage.session_id == session.id,
    ).order_by(ConversationMessage.created_at.desc()).limit(limit).all()
    mensajes.reverse()

    return {
        "user_id": user_id,
        "session_id": session.id,
        "messages": [_serialize_message(msg) for msg in mensajes],
    }
