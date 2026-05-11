"""
Módulo de integración con Google Gemini para asesoría financiera.
Basado en el código del notebook chatbot.ipynb
"""

import os
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

KB_PDF_PATH_ENV = "KB_PDF_PATH"
KB_MAX_PAGES_ENV = "KB_MAX_PAGES"
KB_MAX_CHARS = 1800
KB_CHUNK_SIZE = 900
KB_CHUNK_OVERLAP = 150
_KB_CACHE = {"path": None, "text": None}
FALLBACK_BUSY_MESSAGE = (
    "Ahora mismo el servicio de IA está ocupado. "
    "Intenta de nuevo en un momento. "
    "Si quieres, puedo ayudarte con presupuesto, deudas, ahorro o crédito."
)


# System prompt del asesor financiero
SYSTEM_PROMPT = """
Eres un asesor financiero digital para Colombia.

Tu objetivo es:
- Responder preguntas de finanzas personales (ahorro, presupuesto, deudas, credito, inversiones, seguros, impuestos basicos).
- Dar recomendaciones practicas y realistas.
- Educar con lenguaje sencillo.

Reglas:
- Responde solo temas financieros. Si la pregunta no es de finanzas, pide reformular hacia un tema financiero.
- No uses lenguaje tecnico complejo.
- Se claro, directo y util.
- Prioriza evitar el sobreendeudamiento.
- No uses markdown ni listas numeradas.

Formato de respuesta:
- Diagnostico breve.
- Recomendaciones.
- Explicacion sencilla.
"""


def construir_input_usuario(data, user_data=None):
    """Construir prompt con datos financieros o de encuesta del usuario."""
    if not data:
        return ""

    if any(str(key).startswith("q") for key in data.keys()):
        return construir_contexto_encuesta(data, user_data)

    return f"""
    El usuario tiene la siguiente situación financiera:

    Ingresos mensuales: {data.get('ingresos', 0)}
    Gastos fijos: {data.get('gastos_fijos', 0)}
    Gastos variables: {data.get('gastos_variables', 0)}
    Deudas: {data.get('deudas', 0)}

    Genera recomendaciones financieras personalizadas.
    """


def construir_contexto_finanzas(finance_data, goals_data=None):
    if not finance_data and not goals_data:
        return ""

    lines = []

    if finance_data:
        monthly_income = finance_data.get("monthly_income", 0)
        monthly_fixed = finance_data.get("monthly_fixed", 0)
        monthly_variable = finance_data.get("monthly_variable", 0)
        monthly_expenses = finance_data.get("monthly_expenses", 0)
        savings_capacity = finance_data.get("savings_capacity", 0)
        days_with_records = finance_data.get("days_with_records", 0)
        last_record_date = finance_data.get("last_record_date") or "N/A"
        score = finance_data.get("score")
        score_color = finance_data.get("score_color")
        has_records = finance_data.get("has_records")
        initial_income = finance_data.get("initial_income")
        income_changed = finance_data.get("income_changed")
        income_change = finance_data.get("income_change")
        income_updated_at = finance_data.get("income_updated_at")

        lines.append("Contexto financiero reciente (ultimos 30 dias):")
        lines.append(f"Ingreso mensual actual: {monthly_income}")
        lines.append(f"Gastos fijos: {monthly_fixed}")
        lines.append(f"Gastos variables: {monthly_variable}")
        lines.append(f"Gastos totales: {monthly_expenses}")
        lines.append(f"Capacidad de ahorro: {savings_capacity}")
        lines.append(f"Dias con registros: {days_with_records}")
        lines.append(f"Ultimo registro: {last_record_date}")
        lines.append(f"Score actual: {score} ({score_color})")
        lines.append(f"Tiene registros: {has_records}")

        if initial_income is not None:
            lines.append(f"Ingreso mensual inicial (encuesta): {initial_income}")
        if income_changed is not None:
            estado = "si" if income_changed else "no"
            lines.append(f"Cambio de ingreso mensual: {estado}")
            if income_changed and income_change is not None:
                lines.append(f"Variacion aproximada: {income_change}")
        if income_updated_at:
            lines.append(f"Ultima actualizacion de ingreso: {income_updated_at}")

    if goals_data:
        lines.append("Metas de ahorro activas:")
        for goal in goals_data[:3]:
            lines.append(
                f"- {goal.get('title')}: {goal.get('progress', 0):.1f}%"
                f" (ahorrado {goal.get('total_saved')}, faltante {goal.get('remaining')})"
            )

    return "\n".join(lines)


def construir_contexto_encuesta(profile_data, user_data=None):
    """Construir contexto con respuestas de la encuesta financiera."""
    etiquetas = [
        ("q1", "Conocimiento (dinero en casa pierde valor)"),
        ("q2", "Conocimiento (deuda con intereses)"),
        ("q3", "Definición de ahorrar"),
        ("q4", "Conocimiento (tasa de interés)"),
        ("q5", "Endeudamiento"),
        ("q6", "Estrategia de deudas"),
        ("q7", "Conocimiento (inflación)"),
        ("q8", "Conocimiento (tarjeta crédito)"),
        ("q9", "Diversificación"),
        ("q10", "Control de gastos"),
        ("q11", "Ahorros"),
        ("q12", "Gastos inesperados"),
        ("q13", "Fuente de ingresos"),
        ("q14", "Edad"),
        ("q15", "Nivel educativo"),
        ("q16", "Ingresos mensuales"),
    ]

    nombre = user_data.get("name") if user_data else None
    correo = user_data.get("email") if user_data else None
    encabezado = "Perfil del usuario"
    if nombre or correo:
        encabezado += f" (nombre: {nombre or 'N/A'}, email: {correo or 'N/A'})"

    respuestas = [
        f"- {etiqueta}: {profile_data.get(key, 'N/A')}"
        for key, etiqueta in etiquetas
    ]

    return "\n".join([encabezado, "Respuestas de la encuesta:", *respuestas])


def _perfil_tiene_finanzas(profile_data):
    if not profile_data:
        return False
    claves = {"ingresos", "gastos_fijos", "gastos_variables", "deudas"}
    return any(clave in profile_data for clave in claves)


def _tiene_finanzas(profile_data, finance_data):
    if _perfil_tiene_finanzas(profile_data):
        return True
    if not finance_data:
        return False
    claves = {"monthly_income", "monthly_fixed", "monthly_variable", "monthly_expenses"}
    return any(clave in finance_data for clave in claves)


def _map_finance_to_fallback(finance_data):
    if not finance_data:
        return None
    return {
        "ingresos": finance_data.get("monthly_income", 0),
        "gastos_fijos": finance_data.get("monthly_fixed", 0),
        "gastos_variables": finance_data.get("monthly_variable", 0),
        "deudas": 0,
    }


def limpiar_formato_texto(texto):
    if not texto:
        return texto

    limpio = texto.replace("**", "")
    limpio = limpio.replace("__", "")

    lineas = []
    for linea in limpio.splitlines():
        linea = re.sub(r"^\s*#+\s*", "", linea)
        linea = re.sub(r"^\s*\d+\.\s*", "- ", linea)
        linea = re.sub(r"^\s*[-*]\s*", "- ", linea)
        linea = linea.strip()
        if linea:
            lineas.append(linea)

    return "\n".join(lineas)


def _normalizar_texto(texto):
    palabras = re.findall(r"[a-zA-Z0-9áéíóúñÁÉÍÓÚÑ]+", texto.lower())
    return {p for p in palabras if len(p) > 2}


def _extraer_texto_pdf(pdf_path, max_pages):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    try:
        reader = PdfReader(pdf_path)
        paginas = reader.pages[:max_pages]
        contenido = []
        for pagina in paginas:
            texto = pagina.extract_text() or ""
            if texto:
                contenido.append(texto)
        return "\n".join(contenido).strip()
    except Exception:
        return None


def _seleccionar_fragmento_relevante(texto, consulta, max_chars):
    if not texto:
        return None

    consulta_tokens = _normalizar_texto(consulta)
    if not consulta_tokens:
        return texto[:max_chars]

    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + KB_CHUNK_SIZE, len(texto))
        chunks.append(texto[inicio:fin])
        if fin == len(texto):
            break
        inicio = fin - KB_CHUNK_OVERLAP

    mejor_chunk = None
    mejor_score = -1
    for chunk in chunks:
        tokens = _normalizar_texto(chunk)
        score = len(tokens.intersection(consulta_tokens))
        if score > mejor_score:
            mejor_score = score
            mejor_chunk = chunk

    if not mejor_chunk:
        return None

    return mejor_chunk[:max_chars]


def obtener_contexto_knowledge_base(mensaje):
    """Extraer contexto relevante desde un PDF configurado por variable de entorno."""
    pdf_path = os.getenv(KB_PDF_PATH_ENV)
    if not pdf_path:
        return None

    max_pages = int(os.getenv(KB_MAX_PAGES_ENV, "10"))

    if _KB_CACHE["path"] != pdf_path:
        _KB_CACHE["text"] = _extraer_texto_pdf(pdf_path, max_pages)
        _KB_CACHE["path"] = pdf_path

    texto = _KB_CACHE.get("text")
    if not texto:
        return None

    return _seleccionar_fragmento_relevante(texto, mensaje, KB_MAX_CHARS)


def analizar_usuario(data):
    """Calcular métricas financieras del usuario"""
    ingresos = data.get('ingresos', 0)
    gastos_fijos = data.get('gastos_fijos', 0)
    gastos_variables = data.get('gastos_variables', 0)
    deudas = data.get('deudas', 0)
    
    ahorro = ingresos - (gastos_fijos + gastos_variables)
    deuda_ratio = deudas / ingresos if ingresos > 0 else 0
    
    return {
        'ahorro': ahorro,
        'deuda_ratio': deuda_ratio,
        'total_gastos': gastos_fijos + gastos_variables
    }


def generar_respuesta_ia(
    mensaje,
    perfil_data=None,
    historial_conversacion=None,
    user_data=None,
    finance_data=None,
    goals_data=None,
):
    """
    Generar respuesta del LLM usando Google Gemini.
    
    Args:
        mensaje: str - Pregunta del usuario
        perfil_data: dict - Datos financieros del usuario o encuesta (opcional)
        historial_conversacion: list - Historial de mensajes anteriores [{role, content}, ...] (opcional)
        user_data: dict - Datos del usuario (name, email, etc) (opcional)
        
    Returns:
        str - Respuesta del modelo
    """
    
    if not LANGCHAIN_AVAILABLE:
        return None
    
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        
        # Inicializar modelo
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key
        )
        
        # Construir historial
        history = [SystemMessage(content=SYSTEM_PROMPT)]

        contexto_usuario = construir_input_usuario(perfil_data, user_data)
        if contexto_usuario:
            history.append(SystemMessage(content=contexto_usuario))

        contexto_finanzas = construir_contexto_finanzas(finance_data, goals_data)
        if contexto_finanzas:
            history.append(SystemMessage(content=contexto_finanzas))

        contexto_kb = obtener_contexto_knowledge_base(mensaje)
        if contexto_kb:
            history.append(SystemMessage(
                content="Contexto de referencia (PDF):\n" + contexto_kb
            ))
        
        # Agregar historial previo de la conversación
        if historial_conversacion:
            for msg in historial_conversacion:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    history.append(HumanMessage(content=content))
                elif role == 'assistant':
                    history.append(AIMessage(content=content))
                else:
                    history.append(HumanMessage(content=content))
        
        # Agregar mensaje actual del usuario
        history.append(HumanMessage(content=mensaje))
        
        # Invocar modelo
        response = llm.invoke(history)
        return response.content

    except Exception:
        return None


def generar_respuesta_fallback(mensaje, perfil_data=None):
    """
    Respuesta de fallback cuando no está disponible Google Gemini.
    Análisis básico sin IA.
    """
    if not perfil_data:
        return "Hola, soy tu asesor financiero digital. Cuéntame tu situación financiera para poder ayudarte mejor."
    
    # Análisis básico
    metricas = analizar_usuario(perfil_data)
    ahorro = metricas['ahorro']
    ingresos = perfil_data.get('ingresos', 0)
    
    respuesta = f"Según tus datos financieros: "
    
    if ahorro > 0:
        respuesta += f"tus ingresos (${ingresos:,.0f}) superan tus gastos en ${ahorro:,.0f}. "
        respuesta += "Recomendación: Guarda al menos el 10% de eso en un fondo de emergencia. "
    elif ahorro < 0:
        respuesta += f"estás gastando más de lo que ganas (déficit de ${abs(ahorro):,.0f}). "
        respuesta += "Necesitas revisar tus gastos variables para ajustar. "
    else:
        respuesta += "estás en equilibrio, pero sin margen para ahorrar. "
    
    # Análisis de deudas
    deudas = perfil_data.get('deudas', 0)
    if deudas > ingresos * 1.5:
        respuesta += f"Además, tus deudas son altas. Prioriza pagarlas lo antes posible."
    
    return respuesta


def generar_respuesta_fallback_general():
    """Respuesta general cuando la IA no está disponible."""
    return FALLBACK_BUSY_MESSAGE


def generar_recomendacion_inicial(profile_data, user_data=None):
    """
    Generar una recomendación inicial personalizada para el usuario.
    Se ejecuta la primera vez que entra al chatbot.
    
    Args:
        profile_data: dict - Perfil financiero del usuario (q1-q16)
        user_data: dict - Datos del usuario (name, email, etc)
        
    Returns:
        str - Recomendación inicial basada en el perfil
    """
    
    # Construir prompt inicial con respuestas de la encuesta
    prompt_inicial = f"""
    El usuario acaba de completar una encuesta de educación financiera. Basándote en sus respuestas, 
    genera una recomendación inicial personalizada que sea:
    
    1. Alentadora y positiva
    2. Realista y práctica
    3. En lenguaje sencillo (máximo 5-6 frases)
    4. Sin markdown ni listas numeradas
    
    Respuestas del usuario:
    - Conocimiento (dinero en casa pierde valor): {profile_data.get('q1', 'N/A')}
    - Conocimiento (deuda con intereses): {profile_data.get('q2', 'N/A')}
    - Definición de ahorrar: {profile_data.get('q3', 'N/A')}
    - Conocimiento (tasa de interés): {profile_data.get('q4', 'N/A')}
    - Endeudamiento: {profile_data.get('q5', 'N/A')}
    - Estrategia de deudas: {profile_data.get('q6', 'N/A')}
    - Conocimiento (inflación): {profile_data.get('q7', 'N/A')}
    - Conocimiento (tarjeta crédito): {profile_data.get('q8', 'N/A')}
    - Diversificación: {profile_data.get('q9', 'N/A')}
    - Control de gastos: {profile_data.get('q10', 'N/A')}
    - Ahorros: {profile_data.get('q11', 'N/A')}
    - Gastos inesperados: {profile_data.get('q12', 'N/A')}
    - Fuente de ingresos: {profile_data.get('q13', 'N/A')}
    - Edad: {profile_data.get('q14', 'N/A')}
    - Nivel educativo: {profile_data.get('q15', 'N/A')}
    - Ingresos mensuales: {profile_data.get('q16', 'N/A')}
    
    Genera una bienvenida cálida y una recomendación del primer paso que debe tomar según su perfil.
    """
    
    recomendacion = generar_respuesta_ia(
        prompt_inicial,
        profile_data,
        user_data=user_data,
    )

    if recomendacion:
        return limpiar_formato_texto(recomendacion)

    nombre = user_data.get("name") if user_data else None
    saludo = f"Hola {nombre}. " if nombre else "Hola. "
    return (
        saludo
        + "Gracias por completar tu encuesta financiera. "
        + "El mejor primer paso es registrar tus gastos por una semana para ver en qué se va tu dinero. "
        + "Luego define un ahorro fijo, aunque sea pequeño, y evita nuevas deudas mientras organizas tus cuentas."
    )


def procesar_mensaje_chatbot(
    user_id,
    mensaje,
    user_data=None,
    profile_data=None,
    historial_conversacion=None,
    finance_data=None,
    goals_data=None,
):
    """
    Función principal para procesar mensajes del chatbot.
    
    Args:
        user_id: int - ID del usuario
        mensaje: str - Mensaje del usuario
        user_data: dict - Datos del usuario (name, email, etc)
        profile_data: dict - Perfil financiero del usuario
        historial_conversacion: list - Historial previo [{role, content}, ...]
        
    Returns:
        dict - Respuesta estructurada
    """
    
    # Validar mensaje
    if not mensaje or not mensaje.strip():
        return {
            "error": "El mensaje no puede estar vacío",
            "reply": None
        }
    
    # Generar respuesta
    try:
        reply = generar_respuesta_ia(
            mensaje,
            profile_data,
            historial_conversacion,
            user_data=user_data,
            finance_data=finance_data,
            goals_data=goals_data,
        )

        if not reply:
            if _tiene_finanzas(profile_data, finance_data):
                fallback_data = profile_data
                if not _perfil_tiene_finanzas(profile_data):
                    fallback_data = _map_finance_to_fallback(finance_data)
                reply = generar_respuesta_fallback(mensaje, fallback_data)
            else:
                reply = generar_respuesta_fallback_general()

        reply = limpiar_formato_texto(reply)
        
        return {
            "error": None,
            "reply": reply,
            "user_data": user_data,
            "profile_data": profile_data
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "reply": None
        }

