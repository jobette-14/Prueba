"""Endpoints de datos historicos, importacion CSV y estadisticas."""

import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from datos.carga_csv import leer_csv

from ..seguridad import requerir_api_key
from ..schemas import RegistroEntrada

router = APIRouter(prefix="/api", tags=["Datos"])


@router.get("/registros", summary="Lista los registros historicos")
def listar_registros(request: Request, limite: int = 200) -> dict:
    estado = request.app.state.estado
    registros = estado.gestor.registros()
    return {"total": len(registros), "registros": registros[-limite:]}


@router.post("/registros", summary="Registra un dato historico")
def registrar(request: Request, entrada: RegistroEntrada,
              _: bool = Depends(requerir_api_key)) -> dict:
    estado = request.app.state.estado
    registro = estado.registrar_registro(
        entrada.temperatura, entrada.personas, entrada.horas_uso,
        entrada.consumo_anterior, entrada.consumo_real)
    return {"exitoso": True, "registro": registro}


@router.post("/registros/importar", summary="Importa registros desde un CSV")
async def importar_registros(
    request: Request, archivo: UploadFile = File(...),
    _: bool = Depends(requerir_api_key),
) -> dict:
    estado = request.app.state.estado
    contenido = await archivo.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo esta vacio.")

    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as f:
        f.write(contenido)
        ruta = f.name
    try:
        datos, resumen = leer_csv(ruta)
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass

    if resumen.get("errores"):
        mensajes = "; ".join(e.get("mensaje", "Error") for e in resumen["errores"])
        raise HTTPException(status_code=422, detail=f"Errores en el CSV: {mensajes}")
    if not datos:
        raise HTTPException(status_code=422, detail="No hay datos validos en el CSV.")

    agregados = estado.agregar_registros_masivo(datos)
    return {"exitoso": True, "agregados": agregados, "resumen": resumen}


@router.get("/estadisticas", summary="Estadisticas para el panel principal")
def estadisticas(request: Request) -> dict:
    estado = request.app.state.estado
    return estado.estadisticas()
