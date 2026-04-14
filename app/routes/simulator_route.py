"""
Rutas FastAPI para el Simulador de Crédito
"""

from fastapi import APIRouter, HTTPException
from app.simulador.credit_simulator import (
    obtener_bancos,
    obtener_banco_detail,
    obtener_tipos_credito,
    simular_credito_ruta_a,
    simular_credito_ruta_b,
    obtener_tabla_amortizacion,
)

router = APIRouter()


@router.get("/bancos")
def get_bancos():
    """Retorna lista de bancos disponibles para simular."""
    try:
        bancos = obtener_bancos()
        return {"bancos": bancos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bancos/{banco_id}")
def get_banco_detail(banco_id: int):
    """Retorna detalles completos de un banco específico."""
    try:
        banco = obtener_banco_detail(banco_id)
        if "error" in banco:
            raise HTTPException(status_code=404, detail=banco["error"])
        return banco
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipos")
def get_tipos_credito():
    """Retorna tipos de crédito disponibles."""
    try:
        tipos = obtener_tipos_credito()
        return {"tipos": tipos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simular/ruta-a")
def simular_ruta_a(payload: dict):
    """
    Simula un crédito - Ruta A (usuario sabe el monto).
    
    Payload:
    {
        "capital": 5000000,
        "tipo": 2,
        "plazo": 48,
        "tasa_mensual": 1.75
    }
    """
    try:
        capital = payload.get("capital")
        tipo = payload.get("tipo")
        plazo = payload.get("plazo")
        tasa_p = payload.get("tasa_mensual")
        
        if None in [capital, tipo, plazo, tasa_p]:
            raise HTTPException(status_code=400, detail="Parámetros incompletos")
        
        resultado = simular_credito_ruta_a(capital, tipo, plazo, tasa_p)
        
        if "error" in resultado:
            raise HTTPException(status_code=400, detail=resultado["error"])
        
        return resultado
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simular/ruta-b")
def simular_ruta_b(payload: dict):
    """
    Simula un crédito - Ruta B (usuario sabe la cuota).
    
    Payload:
    {
        "cuota_mensual": 150000,
        "tipo": 2,
        "plazo": 48,
        "tasa_mensual": 1.75
    }
    """
    try:
        cuota = payload.get("cuota_mensual")
        tipo = payload.get("tipo")
        plazo = payload.get("plazo")
        tasa_p = payload.get("tasa_mensual")
        
        if None in [cuota, tipo, plazo, tasa_p]:
            raise HTTPException(status_code=400, detail="Parámetros incompletos")
        
        resultado = simular_credito_ruta_b(cuota, tipo, plazo, tasa_p)
        
        if "error" in resultado:
            raise HTTPException(status_code=400, detail=resultado["error"])
        
        return resultado
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/amortizacion")
def get_amortizacion(payload: dict):
    """
    Retorna tabla de amortización.
    
    Payload:
    {
        "capital": 5000000,
        "tasa_mensual": 1.75,
        "plazo": 48,
        "cuota_mensual": 125000
    }
    """
    try:
        capital = payload.get("capital")
        tasa_p = payload.get("tasa_mensual")
        plazo = payload.get("plazo")
        cuota = payload.get("cuota_mensual")
        
        if None in [capital, tasa_p, plazo, cuota]:
            raise HTTPException(status_code=400, detail="Parámetros incompletos")
        
        tabla = obtener_tabla_amortizacion(capital, tasa_p, plazo, cuota)
        
        return {"tabla": tabla, "filas": len(tabla)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
