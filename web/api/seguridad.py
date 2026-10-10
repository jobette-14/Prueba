"""Seguridad de la API: autenticacion por API key y limites de solicitudes.

Las rutas de escritura (registrar datos, entrenar, registrar consumo real,
chat) requieren el encabezado `X-API-Key` cuando `ELECTROPREDICT_API_KEY` esta
configurada. En desarrollo, sin clave configurada, las rutas quedan abiertas
para facilitar las pruebas locales (se registra una advertencia).
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import Configuracion

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


async def requerir_api_key(
    request: Request, x_api_key: Optional[str] = Header(default=None)
) -> bool:
    """Dependencia que valida el encabezado `X-API-Key` segun la configuracion."""
    config: Configuracion = request.app.state.config
    if not config.escritura_protegida:
        return True
    if not x_api_key or x_api_key != config.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key ausente o invalida.",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return True
