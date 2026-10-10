"""Endpoints del historial de predicciones."""

from fastapi import APIRouter, Depends, HTTPException, Request

from ..seguridad import requerir_api_key
from ..schemas import ConsumoRealEntrada

router = APIRouter(prefix="/api/historial", tags=["Historial"])


@router.get("", summary="Historial de predicciones (mas recientes primero)")
def historial(request: Request, limite: int = 100) -> dict:
    estado = request.app.state.estado
    return {"predicciones": estado.historial(limite)}


@router.post("/consumo-real", summary="Registra el consumo real de una prediccion")
def consumo_real(request: Request, entrada: ConsumoRealEntrada,
                 _: bool = Depends(requerir_api_key)) -> dict:
    estado = request.app.state.estado
    actualizado = estado.registrar_consumo_real(
        entrada.id_prediccion, entrada.consumo_real)
    if actualizado is None:
        raise HTTPException(status_code=404, detail="No se encontro la prediccion.")
    return {"exitoso": True, "prediccion": actualizado}
