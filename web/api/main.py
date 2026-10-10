"""Aplicacion FastAPI de ElectroPredict (version web).

Expone la misma logica de prediccion que la aplicacion de escritorio a traves
de una API REST documentada y sirve el frontend compilado (React/Vite).
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from .config import Configuracion
from .estado import EstadoApp
from .seguridad import limiter
from .routers import salud, modelo, prediccion, datos, historial, reportes, chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config: Configuracion = None, estado: EstadoApp = None) -> FastAPI:
    """Crea la aplicacion FastAPI. Permite inyectar config/estado para pruebas."""
    config = config or Configuracion.desde_entorno()
    estado = estado or EstadoApp(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        resultado = estado.inicializar()
        logger.info(f"Inicializacion: {resultado}")
        yield
        estado.cerrar()

    app = FastAPI(
        title="ElectroPredict API",
        description=(
            "API de prediccion de consumo electrico. Reutiliza la misma logica "
            "de regresion lineal multiple que la aplicacion de escritorio."),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.state.config = config
    app.state.estado = estado
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intenta mas tarde."})

    @app.exception_handler(RequestValidationError)
    async def _validacion_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": "Datos de entrada invalidos.",
                     "errores": exc.errors()})

    @app.exception_handler(Exception)
    async def _error_handler(request: Request, exc: Exception):
        logger.exception("Error no controlado en la API")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor."})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for r in (salud, modelo, prediccion, datos, historial, reportes, chat):
        app.include_router(r.router)

    _montar_frontend(app, config)
    return app


def _montar_frontend(app: FastAPI, config: Configuracion) -> None:
    """Sirve el frontend compilado (dist de Vite) si existe."""
    dist = config.directorio_frontend
    index = os.path.join(dist, "index.html")

    if os.path.isdir(os.path.join(dist, "assets")):
        app.mount("/assets", StaticFiles(
            directory=os.path.join(dist, "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def _index():
        if os.path.isfile(index):
            return FileResponse(index)
        return JSONResponse({
            "nombre": "ElectroPredict API",
            "documentacion": "/api/docs",
            "nota": "El frontend no esta compilado. Ejecute 'npm run build' en web/frontend.",
        })

    @app.get("/{ruta:path}", include_in_schema=False)
    def _spa_fallback(ruta: str):
        # No interceptar rutas de la API ni la documentacion.
        if ruta.startswith("api"):
            return JSONResponse(status_code=404, content={"detail": "No encontrado"})
        archivo = os.path.join(dist, ruta)
        if os.path.isfile(archivo):
            return FileResponse(archivo)
        if os.path.isfile(index):
            return FileResponse(index)
        return JSONResponse(status_code=404, content={"detail": "No encontrado"})


app = create_app()
