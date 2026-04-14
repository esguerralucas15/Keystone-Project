"""
Módulo de Simulador de Crédito de Consumo - Colombia
Adaptado para API REST (retorna diccionarios en lugar de imprimir)
"""

# ─────────────────────────────────────────────────────────────
# [CONFIG] CONFIGURACIÓN DEL SIMULADOR
# ─────────────────────────────────────────────────────────────

TASAS_BANCOS = {
    1: {
        "nombre": "Bancolombia",
        "tasa_min": 1.50,
        "tasa_max": 1.91,
        "tasa_ref": 1.75,
        "tea_ref": 23.14,
        "vigencia": "Abril 2026",
        "nota": "Tasa fija. Puede bajar con nómina Bancolombia.",
    },
    2: {
        "nombre": "Banco de Bogotá",
        "tasa_min": 1.77,
        "tasa_max": 1.91,
        "tasa_ref": 1.90,
        "tea_ref": 25.34,
        "vigencia": "2026",
        "nota": "Tasa según perfil. Plazos de 24 a 72 meses.",
    },
    3: {
        "nombre": "Banco Caja Social",
        "tasa_min": 1.45,
        "tasa_max": 2.81,
        "tasa_ref": 1.80,
        "tea_ref": 23.87,
        "vigencia": "2026",
        "nota": "Rango amplio según perfil. Plazos hasta 60 meses.",
    },
}

RANGOS_PLAZO = {
    1: (12, 36),
    2: (36, 72),
    3: (48, 84),
    4: (12, 120),
}

NOMBRES_TIPO = {
    1: "Crédito pequeño / libre inversión",
    2: "Crédito de consumo estándar",
    3: "Crédito mediano y grande",
    4: "Crédito de libranza",
}

TASA_USURA_MENSUAL = 2.953
TASA_SEGURO_VIDA = 0.035
MONTO_MINIMO = 500_000
MONTO_MAXIMO = 500_000_000


# ─────────────────────────────────────────────────────────────
# [UTILS] FUNCIONES MATEMÁTICAS
# ─────────────────────────────────────────────────────────────

def calcular_cuota(capital: float, tasa_mensual: float, n_meses: int) -> float:
    """Calcula la cuota mensual usando amortización francesa."""
    i = tasa_mensual
    n = n_meses
    if i == 0:
        return capital / n
    cuota = capital * (i * (1 + i) ** n) / ((1 + i) ** n - 1)
    return round(cuota, 0)


def calcular_capital(cuota: float, tasa_mensual: float, n_meses: int) -> float:
    """Calcula el capital máximo dado una cuota mensual."""
    i = tasa_mensual
    n = n_meses
    if i == 0:
        return cuota * n
    capital = cuota * ((1 + i) ** n - 1) / (i * (1 + i) ** n)
    return round(capital, 0)


def tea_desde_mensual(tasa_mensual_pct: float) -> float:
    """Convierte tasa mensual (%) a Tasa Efectiva Anual (%)."""
    i = tasa_mensual_pct / 100
    return round(((1 + i) ** 12 - 1) * 100, 4)


def generar_tabla_amortizacion(capital: float, tasa_mensual: float,
                                n_meses: int, cuota: float) -> list:
    """Genera la tabla de amortización mes a mes."""
    tabla = []
    saldo = capital
    tasa_seguro = TASA_SEGURO_VIDA / 100

    for mes in range(1, n_meses + 1):
        interes = round(saldo * tasa_mensual, 0)
        seguro = round(saldo * tasa_seguro, 0)
        abono_capital = round(cuota - interes, 0)

        if mes == n_meses:
            abono_capital = saldo
            cuota_real = round(interes + abono_capital + seguro, 0)
        else:
            cuota_real = round(cuota + seguro, 0)

        saldo_final = round(saldo - abono_capital, 0)

        tabla.append({
            "mes": mes,
            "saldo_inicial": saldo,
            "interes": interes,
            "abono_capital": abono_capital,
            "seguro": seguro,
            "cuota_total": cuota_real,
            "saldo_final": max(saldo_final, 0),
        })
        saldo = max(saldo_final, 0)

    return tabla


# ─────────────────────────────────────────────────────────────
# [SIMULADOR] FUNCIONES PRINCIPALES
# ─────────────────────────────────────────────────────────────

def obtener_bancos():
    """Retorna lista de bancos disponibles."""
    bancos = []
    for k, banco in TASAS_BANCOS.items():
        bancos.append({
            "id": k,
            "nombre": banco["nombre"],
            "tasa_ref": banco["tasa_ref"],
            "tea_ref": banco["tea_ref"],
        })
    return bancos


def obtener_banco_detail(banco_id: int) -> dict:
    """Retorna detalles completos de un banco."""
    if banco_id not in TASAS_BANCOS:
        return {"error": "Banco no encontrado"}
    
    banco = TASAS_BANCOS[banco_id]
    return {
        "id": banco_id,
        "nombre": banco["nombre"],
        "tasa_min": banco["tasa_min"],
        "tasa_max": banco["tasa_max"],
        "tasa_ref": banco["tasa_ref"],
        "tea_ref": banco["tea_ref"],
        "vigencia": banco["vigencia"],
        "nota": banco["nota"],
    }


def obtener_tipos_credito() -> dict:
    """Retorna tipos de crédito disponibles."""
    tipos = {}
    for k, nombre in NOMBRES_TIPO.items():
        plazo_min, plazo_max = RANGOS_PLAZO[k]
        tipos[k] = {
            "nombre": nombre,
            "plazo_min": plazo_min,
            "plazo_max": plazo_max,
        }
    return tipos


def simular_credito_ruta_a(capital: float, tipo: int, plazo: int, tasa_p: float) -> dict:
    """
    Simula un crédito - Ruta A (usuario sabe el monto).
    
    Args:
        capital: Monto del crédito en COP
        tipo: Tipo de crédito (1-4)
        plazo: Plazo en meses
        tasa_p: Tasa mensual en porcentaje
        
    Returns:
        dict con los resultados de la simulación
    """
    # Validaciones
    if capital < MONTO_MINIMO or capital > MONTO_MAXIMO:
        return {"error": f"Monto debe estar entre ${MONTO_MINIMO:,.0f} y ${MONTO_MAXIMO:,.0f}"}
    
    if tipo not in RANGOS_PLAZO:
        return {"error": "Tipo de crédito inválido"}
    
    plazo_min, plazo_max = RANGOS_PLAZO[tipo]
    if plazo < plazo_min or plazo > plazo_max:
        return {"error": f"Plazo debe estar entre {plazo_min} y {plazo_max} meses"}
    
    # Cálculos
    tasa_d = tasa_p / 100
    cuota = calcular_cuota(capital, tasa_d, plazo)
    total_pago = round(cuota * plazo, 0)
    total_int = round(total_pago - capital, 0)
    tea = tea_desde_mensual(tasa_p)
    
    seguro_estimado = round((capital / 2) * (TASA_SEGURO_VIDA / 100) * plazo, 0)
    ctc = round(total_int + seguro_estimado, 0)
    
    alerta_usura = tasa_p > TASA_USURA_MENSUAL
    
    return {
        "ruta": "A",
        "capital": capital,
        "tipo": tipo,
        "tipo_nombre": NOMBRES_TIPO[tipo],
        "plazo": plazo,
        "tasa_mensual": tasa_p,
        "tea": tea,
        "cuota_mensual": cuota,
        "total_pago": total_pago,
        "total_interes": total_int,
        "seguro_estimado": seguro_estimado,
        "ctc": ctc,
        "alerta_usura": alerta_usura,
        "tasa_usura": TASA_USURA_MENSUAL,
    }


def simular_credito_ruta_b(cuota_usuario: float, tipo: int, plazo: int, tasa_p: float) -> dict:
    """
    Simula un crédito - Ruta B (usuario sabe la cuota).
    
    Args:
        cuota_usuario: Cuota mensual máxima que puede pagar
        tipo: Tipo de crédito (1-4)
        plazo: Plazo en meses
        tasa_p: Tasa mensual en porcentaje
        
    Returns:
        dict con los resultados de la simulación
    """
    if tipo not in RANGOS_PLAZO:
        return {"error": "Tipo de crédito inválido"}
    
    plazo_min, plazo_max = RANGOS_PLAZO[tipo]
    if plazo < plazo_min or plazo > plazo_max:
        return {"error": f"Plazo debe estar entre {plazo_min} y {plazo_max} meses"}
    
    # Calcular capital disponible
    tasa_d = tasa_p / 100
    capital = calcular_capital(cuota_usuario, tasa_d, plazo)
    
    if capital < MONTO_MINIMO:
        return {"error": f"Con esa cuota no alcanzas el monto mínimo de ${MONTO_MINIMO:,.0f}"}
    
    if capital > MONTO_MAXIMO:
        capital = MONTO_MAXIMO
    
    # Recalcular cuota con el capital ajustado
    cuota = calcular_cuota(capital, tasa_d, plazo)
    total_pago = round(cuota * plazo, 0)
    total_int = round(total_pago - capital, 0)
    tea = tea_desde_mensual(tasa_p)
    
    seguro_estimado = round((capital / 2) * (TASA_SEGURO_VIDA / 100) * plazo, 0)
    ctc = round(total_int + seguro_estimado, 0)
    
    alerta_usura = tasa_p > TASA_USURA_MENSUAL
    
    return {
        "ruta": "B",
        "capital": capital,
        "tipo": tipo,
        "tipo_nombre": NOMBRES_TIPO[tipo],
        "plazo": plazo,
        "tasa_mensual": tasa_p,
        "tea": tea,
        "cuota_mensual": cuota,
        "total_pago": total_pago,
        "total_interes": total_int,
        "seguro_estimado": seguro_estimado,
        "ctc": ctc,
        "alerta_usura": alerta_usura,
        "tasa_usura": TASA_USURA_MENSUAL,
    }


def obtener_tabla_amortizacion(capital: float, tasa_p: float, plazo: int, cuota: float) -> list:
    """Retorna tabla de amortización."""
    tasa_d = tasa_p / 100
    return generar_tabla_amortizacion(capital, tasa_d, plazo, cuota)
