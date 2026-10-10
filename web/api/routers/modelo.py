"""Endpoints del modelo: estado, entrenamiento y comparacion de algoritmos."""

from fastapi import APIRouter, Depends, HTTPException, Request

from ..seguridad import requerir_api_key, limiter
from ..schemas import EntrenamientoEntrada

router = APIRouter(prefix="/api/modelo", tags=["Modelo"])


@router.get("", summary="Estado e informacion del modelo actual")
def estado_modelo(request: Request) -> dict:
    estado = request.app.state.estado
    modelo = estado.modelo
    return {
        "entrenado": modelo.entrenado,
        "algoritmo": modelo.algoritmo,
        "algoritmo_nombre": modelo.algoritmo_nombre,
        "version": modelo.version,
        "imputacion": modelo.imputar,
        "metricas": estado.metricas,
        "coeficientes": estado.info_entrenamiento.get("coeficientes", {})
        if estado.info_entrenamiento else {},
        "intercepto": estado.info_entrenamiento.get("intercepto")
        if estado.info_entrenamiento else None,
        "formula": modelo.obtener_formula() if modelo.entrenado else None,
    }


@router.post("/entrenar", summary="Entrena el modelo con los datos historicos")
def entrenar(request: Request, entrada: EntrenamientoEntrada,
             _: bool = Depends(requerir_api_key)) -> dict:
    estado = request.app.state.estado
    resultado = estado.entrenar(
        algoritmo=entrada.algoritmo, imputar=entrada.imputar,
        test_size=entrada.test_size)
    if not resultado.get("exitoso"):
        raise HTTPException(status_code=400, detail=resultado.get("error", "Error"))
    return resultado


@router.post("/comparar", summary="Compara los algoritmos disponibles")
def comparar(request: Request, entrada: EntrenamientoEntrada,
             _: bool = Depends(requerir_api_key)) -> dict:
    from modelo.entrenamiento import comparar_algoritmos
    estado = request.app.state.estado
    datos = estado.gestor.datos_para_entrenamiento()
    if len(datos) < 3:
        raise HTTPException(status_code=400,
                            detail="Se requieren al menos 3 registros historicos.")
    resultados = comparar_algoritmos(datos, test_size=entrada.test_size,
                                     imputar=entrada.imputar)
    return {"resultados": resultados}
