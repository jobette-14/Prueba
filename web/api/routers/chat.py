"""Endpoint del chatbot de IA (pluggable).

Si no hay proveedor configurado (`CHAT_API_KEY`), responde con un mensaje
informativo y la app sigue funcionando sin conexion. La clave del proveedor
vive solo en el servidor y nunca se expone al navegador.
"""

import os
import logging

import httpx
from fastapi import APIRouter, Depends, Request

from ..seguridad import requerir_api_key, limiter
from ..schemas import ChatEntrada

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Chat IA"])

LIMITE = os.getenv("RATE_LIMIT", "120/minute")

_SISTEMA = (
    "Eres el asistente de ElectroPredict, una aplicacion que predice el consumo "
    "electrico con regresion (temperatura, personas, horas de uso y consumo "
    "anterior). Responde en espanol, de forma breve y clara. Si no sabes algo, "
    "dilo. No inventes datos ni credenciales."
)


@router.post("/chat", summary="Chat con el asistente de IA")
@limiter.limit(LIMITE)
async def chat(request: Request, entrada: ChatEntrada,
               _: bool = Depends(requerir_api_key)) -> dict:
    config = request.app.state.config
    if not config.chat_disponible:
        return {
            "disponible": False,
            "respuesta": (
                "El asistente de IA no esta configurado en este servidor. "
                "Puedes seguir usando la prediccion, el historial y los reportes "
                "sin conexion. Un administrador puede activar el chat definiendo "
                "CHAT_API_KEY."),
        }

    mensajes = [{"role": "system", "content": _SISTEMA}]
    for turno in entrada.historial[-6:]:
        rol = turno.get("rol") or turno.get("role")
        texto = turno.get("texto") or turno.get("content")
        if rol in ("user", "usuario", "assistant", "asistente") and texto:
            mensajes.append({
                "role": "assistant" if rol in ("assistant", "asistente") else "user",
                "content": str(texto)[:2000],
            })
    mensajes.append({"role": "user", "content": entrada.mensaje})

    url = config.chat_base_url.rstrip("/") + "/chat/completions"
    payload = {"model": config.chat_model, "messages": mensajes, "max_tokens": 400}

    try:
        async with httpx.AsyncClient(timeout=20.0) as cliente:
            resp = await cliente.post(
                url, json=payload,
                headers={"Authorization": f"Bearer {config.chat_api_key}"})
        if resp.status_code != 200:
            logger.error(f"Proveedor de IA respondio {resp.status_code}")
            return {"disponible": True, "error": True,
                    "respuesta": "El asistente no esta disponible en este momento. "
                                 "Intenta mas tarde."}
        datos = resp.json()
        texto = datos["choices"][0]["message"]["content"].strip()
        return {"disponible": True, "respuesta": texto}
    except (httpx.HTTPError, KeyError, IndexError) as e:
        logger.error(f"Error consultando al proveedor de IA: {e}")
        return {"disponible": True, "error": True,
                "respuesta": "No se pudo contactar al asistente. Revisa la conexion."}
