from dotenv import load_dotenv
import os
from typing import Dict, Any
import traceback

load_dotenv()

# lazy imports will be resolved inside functions to avoid stale import state
ChatGoogleGenerativeAI = None
HumanMessage = None
SystemMessage = None
AIMessage = None
_llm = None


def _ensure_imports():
    global ChatGoogleGenerativeAI, HumanMessage, SystemMessage, AIMessage
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI as _Chat
        from langchain_core.messages import (
            HumanMessage as _HumanMessage,
            SystemMessage as _SystemMessage,
            AIMessage as _AIMessage,
        )
        ChatGoogleGenerativeAI = _Chat
        HumanMessage = _HumanMessage
        SystemMessage = _SystemMessage
        AIMessage = _AIMessage
        return None
    except Exception:
        return traceback.format_exc()


def get_llm():
    """Devuelve una instancia singleton del LLM de Google (langchain wrapper)."""
    global _llm
    err = _ensure_imports()
    if err:
        raise RuntimeError(
            "Paquetes LLM no disponibles. Instala 'langchain_google_genai' y 'langchain-core'.\n" + err
        )

    if _llm is not None:
        return _llm

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY no está configurada en el entorno")

    _llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key,
    )
    return _llm


def _fallback_reply(user: Dict[str, Any], profile: Dict[str, Any], message: str) -> str:
    # Simple deterministic fallback when LLM no está disponible
    name = user.get("name") if user else "usuario"
    parts = [f"Hola {name}. No pude generar una respuesta usando el LLM."]
    if profile:
        parts.append("Basado en tu perfil, consejos generales:")
        parts.append(
            "1) Reduce gastos variables; 2) Prioriza pago de deudas con mayor interés; 3) Intenta ahorrar al menos 5-10% de ingresos."
        )
    else:
        parts.append(
            "Provee tu información financiera (ingresos, gastos, deudas) para recomendaciones personalizadas."
        )
    return " ".join(parts)


def build_messages(user: Dict[str, Any], profile: Dict[str, Any], message: str):
    system_content = (
        """
Eres un asesor financiero digital especializado en ayudar a personas con bajos ingresos en Colombia.

Tu objetivo es:
- Analizar la situación financiera del usuario
- Dar recomendaciones prácticas y realistas
- Educar al usuario con lenguaje sencillo

Reglas:
- Usa máximo 4 frases
- No uses lenguaje técnico complejo
- Sé claro, directo y útil
- Prioriza evitar el sobreendeudamiento
- Da máximo 5 recomendaciones

Formato de respuesta:
1. Diagnóstico breve
2. Recomendaciones
3. Explicación sencilla
"""
    )

    # If message classes are available, build structured messages
    if SystemMessage is None or HumanMessage is None:
        text = system_content + "\n\n"
        text += f"Usuario: {user}\nPerfil: {profile}\nMensaje: {message}"
        return text

    history = [SystemMessage(content=system_content)]
    user_info = f"Nombre: {user.get('name')}\nID: {user.get('id')}\nEmail: {user.get('email')}"
    history.append(HumanMessage(content=user_info))

    if profile:
        profile_text = "\n".join([f"{k}: {v}" for k, v in profile.items()])
    else:
        profile_text = "Sin perfil registrado"

    human = f"Perfil:\n{profile_text}\n\nMensaje:\n{message}\n\nGenera una respuesta siguiendo las reglas anteriores."
    history.append(HumanMessage(content=human))
    return history


def generate_reply(user: Dict[str, Any], profile: Dict[str, Any], message: str) -> str:
    """Genera una respuesta usando el LLM y el contexto del usuario/perfil.
    Si el LLM no está disponible o falta la clave, devuelve un fallback seguro.
    """
    err = _ensure_imports()
    if err:
        # return a safe fallback instead of raising so frontend remains usable
        return _fallback_reply(user, profile, message)

    try:
        llm = get_llm()
    except Exception:
        # missing key or other problem -> fallback
        return _fallback_reply(user, profile, message)

    messages = build_messages(user, profile, message)

    try:
        response = llm.invoke(messages)
    except Exception:
        # if something goes wrong during invoke, return fallback
        return _fallback_reply(user, profile, message)

    if hasattr(response, "content"):
        return response.content
    return str(response)
