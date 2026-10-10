"""Configuracion de la API web de ElectroPredict.

Toda la configuracion sensible (base de datos Neon y claves del proveedor de
IA) se lee EXCLUSIVAMENTE de variables de entorno. Nunca se envia al navegador
ni se incrusta en el codigo distribuido.
"""

import os
from dataclasses import dataclass, field
from typing import List


def _bool_env(nombre: str, defecto: bool = False) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in ("1", "true", "yes", "si", "on")


def _lista_env(nombre: str, defecto: List[str]) -> List[str]:
    valor = os.getenv(nombre)
    if not valor:
        return list(defecto)
    return [x.strip() for x in valor.split(",") if x.strip()]


@dataclass
class Configuracion:
    """Configuracion de la aplicacion leida del entorno."""

    entorno: str = "desarrollo"
    # Seguridad
    api_key: str = ""
    rate_limit: str = "120/minute"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    # Base de datos (server-side, nunca se expone)
    database_url: str = ""
    # Modelo
    directorio_modelos: str = ""
    # Chat de IA (pluggable; desactivado si no hay clave)
    chat_enabled: bool = False
    chat_api_key: str = ""
    chat_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"
    # Frontend compilado (dist de Vite) a servir como estatico
    directorio_frontend: str = ""

    @classmethod
    def desde_entorno(cls) -> "Configuracion":
        raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chat_key = os.getenv("CHAT_API_KEY", "").strip()
        return cls(
            entorno=os.getenv("ENTORNO", "desarrollo").strip(),
            api_key=os.getenv("ELECTROPREDICT_API_KEY", "").strip(),
            rate_limit=os.getenv("RATE_LIMIT", "120/minute").strip(),
            cors_origins=_lista_env("CORS_ORIGINS", ["*"]),
            database_url=os.getenv("DATABASE_URL", "").strip(),
            directorio_modelos=os.getenv(
                "MODELOS_DIR", os.path.join(raiz, "modelos")).strip(),
            chat_enabled=_bool_env("CHAT_ENABLED", bool(chat_key)),
            chat_api_key=chat_key,
            chat_base_url=os.getenv("CHAT_BASE_URL", "https://api.openai.com/v1").strip(),
            chat_model=os.getenv("CHAT_MODEL", "gpt-4o-mini").strip(),
            directorio_frontend=os.getenv(
                "FRONTEND_DIR", os.path.join(raiz, "web", "frontend", "dist")).strip(),
        )

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower() in ("produccion", "production", "prod")

    @property
    def escritura_protegida(self) -> bool:
        """Indica si las rutas de escritura exigen API key."""
        return bool(self.api_key)

    @property
    def chat_disponible(self) -> bool:
        return bool(self.chat_enabled and self.chat_api_key)
