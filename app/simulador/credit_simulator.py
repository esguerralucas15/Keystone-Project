"""
Módulo de Simulador de Crédito - Colombia
Adaptado para API REST (retorna diccionarios en lugar de imprimir).
"""

# ─────────────────────────────────────────────────────────────
# [CONFIG] CONFIGURACIÓN DEL SIMULADOR
# ─────────────────────────────────────────────────────────────

TASA_USURA_MENSUAL = 2.953
SEGURO_PORCENTAJE_ESTIMADO = 0.00035


def tasa_mensual_desde_tea(tea_pct: float) -> float:
    """Convierte TEA (%) a tasa mensual efectiva (%)."""
    if tea_pct <= -100:
        return 0
    i = tea_pct / 100
    return round(((1 + i) ** (1 / 12) - 1) * 100, 4)


PRODUCTOS = {
    101: {
        "banco_id": 1,
        "nombre": "Libre Inversion - Tasa fija, cuota fija",
        "categoria": "consumo",
        "tasa_mensual": 1.78,
        "tea_ref": 23.14,
        "cuota_tipo": "fija",
        "seguro_tipo": "fijo",
        "seguro_valor": 23027,
        "seguro_opcional": False,
        "tasa_editable": False,
        "monto_min": 1_000_000,
        "monto_max": 500_000_000,
        "plazo_min": 48,
        "plazo_max": 84,
        "edad_min": 18,
        "edad_max": 84,
        "ingreso_min": None,
        "nota": "Tasa fija con cuota fija. Seguro de vida mensual fijo.",
    },
    102: {
        "banco_id": 1,
        "nombre": "Libre Inversion - Tasa variable, cuota fija",
        "categoria": "consumo",
        "tasa_mensual": 1.84,
        "tea_ref": 24.59,
        "cuota_tipo": "fija",
        "seguro_tipo": "fijo",
        "seguro_valor": 22742,
        "seguro_opcional": False,
        "tasa_editable": False,
        "monto_min": 1_000_000,
        "monto_max": 500_000_000,
        "plazo_min": 48,
        "plazo_max": 84,
        "edad_min": 18,
        "edad_max": 84,
        "ingreso_min": None,
        "nota": "Tasa variable con cuota fija. Seguro de vida mensual fijo.",
    },
    103: {
        "banco_id": 1,
        "nombre": "Libre Inversion - Tasa variable, cuota variable",
        "categoria": "consumo",
        "tasa_mensual": 1.84,
        "tea_ref": 24.59,
        "cuota_tipo": "variable",
        "seguro_tipo": "fijo",
        "seguro_valor": 18288,
        "seguro_opcional": False,
        "tasa_editable": False,
        "monto_min": 1_000_000,
        "monto_max": 500_000_000,
        "plazo_min": 48,
        "plazo_max": 84,
        "edad_min": 18,
        "edad_max": 84,
        "ingreso_min": None,
        "nota": "Tasa variable con cuota variable. Seguro de vida mensual fijo.",
    },
    201: {
        "banco_id": 2,
        "nombre": "Libre Destino",
        "categoria": "consumo",
        "tasa_mensual": 2.08,
        "tea_ref": 28.07,
        "cuota_tipo": "fija",
        "seguro_tipo": "none",
        "seguro_valor": 0,
        "seguro_opcional": False,
        "tasa_editable": False,
        "monto_min": 400_000,
        "monto_max": 500_000_000,
        "plazo_min": 12,
        "plazo_max": 72,
        "edad_min": 18,
        "edad_max": 69,
        "ingreso_min": 1_423_500,
        "nota": "Tasa fija mes vencido. Seguro de vida obligatorio no incluido en el calculo.",
    },
    202: {
        "banco_id": 2,
        "nombre": "Vivienda VIS",
        "categoria": "vivienda",
        "tasa_mensual": tasa_mensual_desde_tea(15.25),
        "tea_ref": 15.25,
        "plazos_anos": [5, 10, 15, 20],
        "edad_min": 18,
        "edad_max": 84,
        "ratio_ingreso": 0.35,
        "financiacion": 0.80,
        "nota": "Simulacion estimada con cuota maxima del 35% del ingreso.",
    },
    203: {
        "banco_id": 2,
        "nombre": "Vivienda No VIS",
        "categoria": "vivienda",
        "tasa_mensual": tasa_mensual_desde_tea(16.49),
        "tea_ref": 16.49,
        "plazos_anos": [5, 10, 15, 20],
        "edad_min": 18,
        "edad_max": 84,
        "ratio_ingreso": 0.42,
        "financiacion": 0.70,
        "nota": "Simulacion estimada con cuota maxima del 42% del ingreso.",
    },
    301: {
        "banco_id": 3,
        "nombre": "Credito Personal (Libre Destino)",
        "categoria": "consumo",
        "tasa_mensual": tasa_mensual_desde_tea(26.70),
        "tea_ref": 26.70,
        "cuota_tipo": "fija",
        "seguro_tipo": "porcentaje",
        "seguro_valor": SEGURO_PORCENTAJE_ESTIMADO,
        "seguro_opcional": True,
        "tasa_editable": True,
        "monto_min": 1_000_000,
        "monto_max": 500_000_000,
        "plazo_min": 6,
        "plazo_max": 60,
        "edad_min": None,
        "edad_max": None,
        "ingreso_min": None,
        "nota": "La tasa es referencial. Puedes editarla. Seguro opcional estimado.",
    },
    302: {
        "banco_id": 3,
        "nombre": "Credito de Libranza",
        "categoria": "consumo",
        "tasa_mensual": tasa_mensual_desde_tea(26.20),
        "tea_ref": 26.20,
        "cuota_tipo": "fija",
        "seguro_tipo": "porcentaje",
        "seguro_valor": SEGURO_PORCENTAJE_ESTIMADO,
        "seguro_opcional": True,
        "tasa_editable": True,
        "monto_min": 1_000_000,
        "monto_max": 500_000_000,
        "plazo_min": 6,
        "plazo_max": 120,
        "edad_min": None,
        "edad_max": None,
        "ingreso_min": None,
        "nota": "La tasa es referencial. Puedes editarla. Seguro opcional estimado.",
    },
}

BANCOS = {
    1: {
        "nombre": "Bancolombia",
        "descripcion": "Credito Libre Inversion (18-84 anos).",
        "productos": [101, 102, 103],
    },
    2: {
        "nombre": "Banco de Bogota",
        "descripcion": "Libre Destino y Vivienda.",
        "productos": [201, 202, 203],
    },
    3: {
        "nombre": "Banco Caja Social",
        "descripcion": "Credito Personal y Libranza.",
        "productos": [301, 302],
    },
}


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


def generar_tabla_amortizacion(
    capital: float,
    tasa_mensual: float,
    n_meses: int,
    cuota_base: float,
    seguro_tipo: str,
    seguro_valor: float,
    incluye_seguro: bool,
) -> list:
    """Genera la tabla de amortización mes a mes."""
    tabla = []
    saldo = capital

    for mes in range(1, n_meses + 1):
        interes = round(saldo * tasa_mensual, 0)
        if incluye_seguro:
            if seguro_tipo == "fijo":
                seguro = round(seguro_valor, 0)
            elif seguro_tipo == "porcentaje":
                seguro = round(saldo * seguro_valor, 0)
            else:
                seguro = 0
        else:
            seguro = 0

        abono_capital = round(cuota_base - interes, 0)

        if mes == n_meses:
            abono_capital = saldo
            cuota_real = round(interes + abono_capital + seguro, 0)
        else:
            cuota_real = round(cuota_base + seguro, 0)

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

def _producto_publico(producto_id: int) -> dict:
    producto = PRODUCTOS[producto_id]
    base = {
        "id": producto_id,
        "banco_id": producto["banco_id"],
        "nombre": producto["nombre"],
        "categoria": producto["categoria"],
        "tasa_mensual": producto["tasa_mensual"],
        "tea_ref": producto["tea_ref"],
        "nota": producto.get("nota"),
    }

    if producto["categoria"] == "consumo":
        base.update({
            "monto_min": producto["monto_min"],
            "monto_max": producto["monto_max"],
            "plazo_min": producto["plazo_min"],
            "plazo_max": producto["plazo_max"],
            "edad_min": producto.get("edad_min"),
            "edad_max": producto.get("edad_max"),
            "ingreso_min": producto.get("ingreso_min"),
            "cuota_tipo": producto.get("cuota_tipo"),
            "seguro_tipo": producto.get("seguro_tipo"),
            "seguro_valor": producto.get("seguro_valor"),
            "seguro_opcional": producto.get("seguro_opcional", False),
            "tasa_editable": producto.get("tasa_editable", False),
        })
    else:
        base.update({
            "plazos_anos": producto.get("plazos_anos", []),
            "edad_min": producto.get("edad_min"),
            "edad_max": producto.get("edad_max"),
            "ratio_ingreso": producto.get("ratio_ingreso"),
            "financiacion": producto.get("financiacion"),
        })

    return base


def obtener_bancos():
    """Retorna lista de bancos disponibles."""
    bancos = []
    for banco_id, banco in BANCOS.items():
        bancos.append({
            "id": banco_id,
            "nombre": banco["nombre"],
            "descripcion": banco["descripcion"],
        })
    return bancos


def obtener_banco_detail(banco_id: int) -> dict:
    """Retorna detalles completos de un banco."""
    if banco_id not in BANCOS:
        return {"error": "Banco no encontrado"}

    banco = BANCOS[banco_id]
    return {
        "id": banco_id,
        "nombre": banco["nombre"],
        "descripcion": banco["descripcion"],
        "productos": [_producto_publico(pid) for pid in banco["productos"]],
    }


def obtener_tipos_credito() -> dict:
    """Retorna productos disponibles (compatibilidad)."""
    return {pid: _producto_publico(pid) for pid in PRODUCTOS}


def _resolver_producto(producto_id: int | None) -> dict:
    if not producto_id or producto_id not in PRODUCTOS:
        return {"error": "Producto no encontrado"}
    return PRODUCTOS[producto_id]


def _validar_requisitos(producto: dict, edad: int | None, ingreso: float | None) -> str | None:
    if producto.get("edad_min") is not None or producto.get("edad_max") is not None:
        if edad is None:
            return "Debes ingresar tu edad para este producto"
        if producto.get("edad_min") is not None and edad < producto["edad_min"]:
            return f"Edad minima {producto['edad_min']} anos"
        if producto.get("edad_max") is not None and edad > producto["edad_max"]:
            return f"Edad maxima {producto['edad_max']} anos"

    if producto.get("ingreso_min") is not None:
        if ingreso is None:
            return "Debes ingresar tu ingreso mensual para este producto"
        if ingreso < producto["ingreso_min"]:
            return f"Ingreso minimo ${producto['ingreso_min']:,.0f}"

    return None


def _resolver_tasa_mensual(producto: dict, tasa_manual: float | None) -> float:
    if tasa_manual is not None and producto.get("tasa_editable"):
        return float(tasa_manual)
    return float(producto["tasa_mensual"])


def _seguro_total_estimado(producto: dict, capital: float, plazo: int, incluye_seguro: bool) -> float:
    if producto.get("seguro_opcional") and not incluye_seguro:
        return 0
    tipo = producto.get("seguro_tipo", "none")
    valor = producto.get("seguro_valor", 0)
    if tipo == "fijo":
        return round(valor * plazo, 0)
    if tipo == "porcentaje":
        return round((capital / 2) * valor * plazo, 0)
    return 0


def simular_credito_ruta_a(
    capital: float,
    producto_id: int,
    plazo: int,
    tasa_p: float | None,
    edad: int | None,
    ingreso_mensual: float | None,
    incluye_seguro: bool,
) -> dict:
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
    producto = _resolver_producto(producto_id)
    if "error" in producto:
        return producto

    if producto["categoria"] != "consumo":
        return {"error": "Este producto solo se simula en la seccion de vivienda"}

    requisito_error = _validar_requisitos(producto, edad, ingreso_mensual)
    if requisito_error:
        return {"error": requisito_error}

    if capital < producto["monto_min"] or capital > producto["monto_max"]:
        return {
            "error": f"Monto debe estar entre ${producto['monto_min']:,.0f} y ${producto['monto_max']:,.0f}"
        }

    if plazo < producto["plazo_min"] or plazo > producto["plazo_max"]:
        return {"error": f"Plazo debe estar entre {producto['plazo_min']} y {producto['plazo_max']} meses"}

    tasa_mensual = _resolver_tasa_mensual(producto, tasa_p)
    tasa_d = tasa_mensual / 100
    cuota_base = calcular_cuota(capital, tasa_d, plazo)
    seguro_mensual = producto.get("seguro_valor", 0) if producto.get("seguro_tipo") == "fijo" else 0
    if producto.get("seguro_opcional") and not incluye_seguro:
        seguro_mensual = 0

    cuota_total = round(cuota_base + seguro_mensual, 0)
    total_pago_base = round(cuota_base * plazo, 0)
    total_interes = round(total_pago_base - capital, 0)
    seguro_estimado = _seguro_total_estimado(producto, capital, plazo, incluye_seguro)
    total_pago = round(total_pago_base + seguro_estimado, 0)
    ctc = round(total_interes + seguro_estimado, 0)
    tea = tea_desde_mensual(tasa_mensual)
    alerta_usura = tasa_mensual > TASA_USURA_MENSUAL

    return {
        "simulacion": "consumo",
        "ruta": "A",
        "producto_id": producto_id,
        "banco": BANCOS[producto["banco_id"]]["nombre"],
        "producto_nombre": producto["nombre"],
        "cuota_tipo": producto.get("cuota_tipo"),
        "capital": capital,
        "plazo": plazo,
        "tasa_mensual": tasa_mensual,
        "tea": tea,
        "cuota_base": cuota_base,
        "cuota_mensual": cuota_total,
        "seguro_mensual": seguro_mensual,
        "seguro_estimado": seguro_estimado,
        "total_pago": total_pago,
        "total_interes": total_interes,
        "ctc": ctc,
        "incluye_seguro": incluye_seguro,
        "seguro_tipo": producto.get("seguro_tipo"),
        "alerta_usura": alerta_usura,
        "tasa_usura": TASA_USURA_MENSUAL,
    }


def simular_credito_ruta_b(
    cuota_usuario: float,
    producto_id: int,
    plazo: int,
    tasa_p: float | None,
    edad: int | None,
    ingreso_mensual: float | None,
    incluye_seguro: bool,
) -> dict:
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
    producto = _resolver_producto(producto_id)
    if "error" in producto:
        return producto

    if producto["categoria"] != "consumo":
        return {"error": "Este producto solo se simula en la seccion de vivienda"}

    requisito_error = _validar_requisitos(producto, edad, ingreso_mensual)
    if requisito_error:
        return {"error": requisito_error}

    if plazo < producto["plazo_min"] or plazo > producto["plazo_max"]:
        return {"error": f"Plazo debe estar entre {producto['plazo_min']} y {producto['plazo_max']} meses"}

    tasa_mensual = _resolver_tasa_mensual(producto, tasa_p)
    tasa_d = tasa_mensual / 100

    seguro_mensual = 0
    if producto.get("seguro_tipo") == "fijo":
        seguro_mensual = producto.get("seguro_valor", 0)
        if producto.get("seguro_opcional") and not incluye_seguro:
            seguro_mensual = 0

    cuota_base = cuota_usuario - seguro_mensual
    if cuota_base <= 0:
        return {"error": "La cuota no alcanza para cubrir el seguro mensual"}

    capital = calcular_capital(cuota_base, tasa_d, plazo)

    if capital < producto["monto_min"]:
        return {"error": f"Con esa cuota no alcanzas el monto minimo de ${producto['monto_min']:,.0f}"}

    if capital > producto["monto_max"]:
        capital = producto["monto_max"]

    cuota_base = calcular_cuota(capital, tasa_d, plazo)
    cuota_total = round(cuota_base + seguro_mensual, 0)
    total_pago_base = round(cuota_base * plazo, 0)
    total_interes = round(total_pago_base - capital, 0)
    seguro_estimado = _seguro_total_estimado(producto, capital, plazo, incluye_seguro)
    total_pago = round(total_pago_base + seguro_estimado, 0)
    ctc = round(total_interes + seguro_estimado, 0)
    tea = tea_desde_mensual(tasa_mensual)
    alerta_usura = tasa_mensual > TASA_USURA_MENSUAL

    return {
        "simulacion": "consumo",
        "ruta": "B",
        "producto_id": producto_id,
        "banco": BANCOS[producto["banco_id"]]["nombre"],
        "producto_nombre": producto["nombre"],
        "cuota_tipo": producto.get("cuota_tipo"),
        "capital": capital,
        "plazo": plazo,
        "tasa_mensual": tasa_mensual,
        "tea": tea,
        "cuota_base": cuota_base,
        "cuota_mensual": cuota_total,
        "seguro_mensual": seguro_mensual,
        "seguro_estimado": seguro_estimado,
        "total_pago": total_pago,
        "total_interes": total_interes,
        "ctc": ctc,
        "incluye_seguro": incluye_seguro,
        "seguro_tipo": producto.get("seguro_tipo"),
        "alerta_usura": alerta_usura,
        "tasa_usura": TASA_USURA_MENSUAL,
    }


def simular_credito_vivienda(
    producto_id: int,
    ingreso_mensual: float,
    edad: int,
    plazo_anos: int,
    solicitantes: int,
    modalidad: str,
) -> dict:
    producto = _resolver_producto(producto_id)
    if "error" in producto:
        return producto
    if producto["categoria"] != "vivienda":
        return {"error": "Producto no disponible para vivienda"}

    if ingreso_mensual <= 0:
        return {"error": "Ingresa un ingreso mensual valido"}

    if edad < producto.get("edad_min", 0) or edad > producto.get("edad_max", 200):
        return {"error": "Edad fuera del rango permitido"}

    if plazo_anos not in producto.get("plazos_anos", []):
        return {"error": "Plazo no permitido para este producto"}

    if solicitantes not in (1, 2):
        return {"error": "Numero de solicitantes invalido"}

    if edad + plazo_anos > producto.get("edad_max", 84):
        return {"error": "El plazo supera la edad maxima al finalizar el credito"}

    ingreso_total = ingreso_mensual * solicitantes
    cuota_max = round(ingreso_total * producto["ratio_ingreso"], 0)
    tasa_mensual = producto["tasa_mensual"]
    plazo_meses = plazo_anos * 12

    capital = calcular_capital(cuota_max, tasa_mensual / 100, plazo_meses)
    valor_vivienda = round(capital / producto["financiacion"], 0)
    cuota_inicial = round(valor_vivienda - capital, 0)

    return {
        "simulacion": "vivienda",
        "producto_id": producto_id,
        "banco": BANCOS[producto["banco_id"]]["nombre"],
        "producto_nombre": producto["nombre"],
        "modalidad": modalidad,
        "solicitantes": solicitantes,
        "plazo_anios": plazo_anos,
        "plazo_meses": plazo_meses,
        "tasa_mensual": tasa_mensual,
        "tea": producto["tea_ref"],
        "ingreso_mensual": ingreso_total,
        "cuota_max": cuota_max,
        "capital": capital,
        "valor_vivienda": valor_vivienda,
        "cuota_inicial": cuota_inicial,
        "financiacion": producto["financiacion"],
    }


def obtener_tabla_amortizacion(
    capital: float,
    tasa_p: float,
    plazo: int,
    cuota_base: float,
    producto_id: int,
    incluye_seguro: bool,
) -> list:
    """Retorna tabla de amortización."""
    producto = _resolver_producto(producto_id)
    if "error" in producto:
        return []

    seguro_tipo = producto.get("seguro_tipo", "none")
    seguro_valor = producto.get("seguro_valor", 0)

    if producto.get("seguro_opcional") and not incluye_seguro:
        seguro_tipo = "none"
        seguro_valor = 0

    tasa_d = tasa_p / 100
    return generar_tabla_amortizacion(
        capital,
        tasa_d,
        plazo,
        cuota_base,
        seguro_tipo,
        seguro_valor,
        incluye_seguro,
    )
