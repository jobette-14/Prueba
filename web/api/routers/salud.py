"""Endpoints de salud y configuracion publica (no sensible)."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["Sistema"])

VERSION_API = "1.0.0"


@router.get("/salud", summary="Estado del servicio")
def salud(request: Request) -> dict:
    """Comprueba que la API responde e informa del estado general."""
    estado = request.app.state.estado
    return {
        "estado": "ok",
        "version_api": VERSION_API,
        "modelo_entrenado": estado.modelo.entrenado,
        "base_datos_conectada": estado.gestor.tiene_persistencia,
    }


@router.get("/config-publica", summary="Configuracion no sensible para el cliente")
def config_publica(request: Request) -> dict:
    """Expone solo datos NO sensibles que el frontend necesita conocer.

    Nunca devuelve la URL de Neon ni claves del proveedor de IA.
    """
    config = request.app.state.config
    estado = request.app.state.estado
    return {
        "version_api": VERSION_API,
        "entorno": config.entorno,
        "chat_disponible": config.chat_disponible,
        "escritura_protegida": config.escritura_protegida,
        "modelo_entrenado": estado.modelo.entrenado,
    }
