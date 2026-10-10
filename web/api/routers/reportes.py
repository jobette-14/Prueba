"""Endpoints de reportes descargables (TXT, CSV, PDF)."""

import os
import tempfile

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse

from reportes.generador import (
    generar_reporte_texto, exportar_reporte_csv, generar_reporte_pdf,
    reportlab_disponible,
)

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


@router.get("/txt", summary="Reporte completo en texto")
def reporte_txt(request: Request):
    estado = request.app.state.estado
    contenido = generar_reporte_texto(
        estado.gestor, estado.modelo, estado.metricas, estado.info_entrenamiento)
    return PlainTextResponse(
        contenido, media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="reporte_electropredict.txt"'})


@router.get("/csv", summary="Reporte tabular en CSV (predicciones o historicos)")
def reporte_csv(request: Request, tipo: str = "predicciones"):
    estado = request.app.state.estado
    if tipo not in ("predicciones", "historicos"):
        raise HTTPException(status_code=400,
                            detail="tipo debe ser 'predicciones' o 'historicos'.")
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                     encoding="utf-8", newline="") as f:
        ruta = f.name
    if not exportar_reporte_csv(estado.gestor, ruta, tipo):
        os.remove(ruta)
        raise HTTPException(status_code=500, detail="No se pudo generar el CSV.")
    return FileResponse(ruta, media_type="text/csv",
                        filename=f"reporte_{tipo}.csv")


@router.get("/pdf", summary="Reporte en PDF")
def reporte_pdf(request: Request):
    if not reportlab_disponible():
        raise HTTPException(status_code=503,
                            detail="La generacion de PDF no esta disponible (falta reportlab).")
    estado = request.app.state.estado
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as f:
        ruta = f.name
    ok = generar_reporte_pdf(
        estado.gestor, estado.modelo, estado.metricas,
        estado.info_entrenamiento, ruta)
    if not ok:
        try:
            os.remove(ruta)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail="No se pudo generar el PDF.")
    return FileResponse(ruta, media_type="application/pdf",
                        filename="reporte_electropredict.pdf")
