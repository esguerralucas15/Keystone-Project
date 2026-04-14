"""
Módulo de integración con Google Gemini para asesoría financiera.
Basado en el código del notebook chatbot.ipynb
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# System prompt del asesor financiero
SYSTEM_PROMPT = """
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


def construir_input_usuario(data):
    """Construir prompt con datos financieros del usuario"""
    return f"""
    El usuario tiene la siguiente situación financiera:

    Ingresos mensuales: {data.get('ingresos', 0)}
    Gastos fijos: {data.get('gastos_fijos', 0)}
    Gastos variables: {data.get('gastos_variables', 0)}
    Deudas: {data.get('deudas', 0)}

    Genera recomendaciones financieras personalizadas.
    """


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


def generar_respuesta_ia(mensaje, perfil_data=None):
    """
    Generar respuesta del LLM usando Google Gemini.
    
    Args:
        mensaje: str - Pregunta del usuario
        perfil_data: dict - Datos financieros del usuario (opcional)
        
    Returns:
        str - Respuesta del modelo
    """
    
    if not LANGCHAIN_AVAILABLE:
        return generar_respuesta_fallback(mensaje, perfil_data)
    
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "⚠️ Error: No se encontró GOOGLE_API_KEY. Configura tu archivo .env"
        
        # Inicializar modelo
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key
        )
        
        # Construir historial
        history = []
        history.append(SystemMessage(content=SYSTEM_PROMPT))
        
        # Agregar contexto financiero si existe
        if perfil_data:
            context_msg = construir_input_usuario(perfil_data)
            history.append(HumanMessage(content=context_msg))
        
        # Agregar mensaje del usuario
        history.append(HumanMessage(content=mensaje))
        
        # Invocar modelo
        response = llm.invoke(history)
        return response.content
        
    except Exception as e:
        return f"❌ Error al generar respuesta: {str(e)}"


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
    total_gastos = metricas['total_gastos']
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
    
    return generar_respuesta_ia(prompt_inicial, profile_data)


def procesar_mensaje_chatbot(user_id, mensaje, user_data=None, profile_data=None):
    """
    Función principal para procesar mensajes del chatbot.
    
    Args:
        user_id: int - ID del usuario
        mensaje: str - Mensaje del usuario
        user_data: dict - Datos del usuario (name, email, etc)
        profile_data: dict - Perfil financiero del usuario
        
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
        reply = generar_respuesta_ia(mensaje, profile_data)
        
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

