"""Endpoints de prediccion individual y por lotes."""

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from ..seguridad import requerir_api_key, limiter
from ..schemas import PrediccionEntrada, PrediccionSalida, LoteEntrada

router = APIRouter(prefix="/api/prediccion", tags=["Prediccion"])

LIMITE = os.getenv("RATE_LIMIT", "120/minute")


@router.post("", response_model=PrediccionSalida,
             summary="Prediccion individual de consumo")
@limiter.limit(LIMITE)
def predecir(request: Request, entrada: PrediccionEntrada) -> dict:
    estado = request.app.state.estado
    if not estado.modelo.entrenado:
        raise HTTPException(
            status_code=409,
            detail="El modelo no esta entrenado. Un administrador debe entrenarlo.")
    resultado = estado.predecir(
        entrada.temperatura, entrada.personas, entrada.horas_uso,
        entrada.consumo_anterior, entrada.consumo_real)
    if not resultado.get("exitoso"):
        raise HTTPException(status_code=422,
                            detail=resultado.get("error", "Prediccion invalida"))
    return resultado


@router.post("/lotes", summary="Prediccion por lotes desde un archivo CSV")
@limiter.limit(LIMITE)
async def predecir_lotes_endpoint(
    request: Request, archivo: UploadFile = File(...),
    _: bool = Depends(requerir_api_key),
) -> dict:
    estado = request.app.state.estado
    if not estado.modelo.entrenado:
        raise HTTPException(status_code=409, detail="El modelo no esta entrenado.")

    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo esta vacio.")

    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as f:
        f.write(contenido)
        ruta = f.name
    try:
        lote = archivo.filename
        resultado = estado.predecir_desde_csv(ruta, lote=lote)
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass

    if not resultado.get("exitoso"):
        raise HTTPException(status_code=422, detail=resultado.get("error"))
    return resultado


@router.post("/lotes/json", summary="Prediccion por lotes desde filas JSON")
@limiter.limit(LIMITE)
def predecir_lotes_json(request: Request, entrada: LoteEntrada,
                        _: bool = Depends(requerir_api_key)) -> dict:
    estado = request.app.state.estado
    if not estado.modelo.entrenado:
        raise HTTPException(status_code=409, detail="El modelo no esta entrenado.")
    filas = [f.model_dump(exclude_none=True) for f in entrada.filas]
    resultado = estado.predecir_lote_filas(filas, lote=entrada.lote)
    if not resultado.get("exitoso"):
        raise HTTPException(status_code=422, detail=resultado.get("error"))
    return resultado
