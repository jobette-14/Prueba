"""Esquemas Pydantic de la API.

Los rangos replican los de `datos/validaciones.py` para que la API web y la
aplicacion de escritorio validen exactamente igual. La validacion de rangos se
delega ademas al nucleo compartido durante el calculo.
"""

from typing import List, Optional
from typing import Literal

from pydantic import BaseModel, Field


class PrediccionEntrada(BaseModel):
    temperatura: float = Field(..., ge=-50, le=60, description="Temperatura en C")
    personas: int = Field(..., ge=1, le=50, description="Numero de personas")
    horas_uso: float = Field(..., ge=0, le=24, description="Horas de uso")
    consumo_anterior: float = Field(..., ge=0, le=1000, description="Consumo anterior en kWh")
    consumo_real: Optional[float] = Field(
        None, ge=0, le=1000, description="Consumo real (opcional) para calcular el error")


class PrediccionSalida(BaseModel):
    exitoso: bool
    consumo_estimado: Optional[float] = None
    consumo_real: Optional[float] = None
    error: Optional[float] = None
    error_absoluto: Optional[float] = None
    algoritmo: Optional[str] = None
    version: Optional[str] = None
    mensaje_error: Optional[str] = None


class RegistroEntrada(BaseModel):
    temperatura: float = Field(..., ge=-50, le=60)
    personas: int = Field(..., ge=1, le=50)
    horas_uso: float = Field(..., ge=0, le=24)
    consumo_anterior: float = Field(..., ge=0, le=1000)
    consumo_real: float = Field(..., ge=0, le=1000)


class LoteEntrada(BaseModel):
    filas: List[PrediccionEntrada] = Field(..., min_length=1)
    lote: Optional[str] = None


class EntrenamientoEntrada(BaseModel):
    algoritmo: Literal["lineal", "ridge", "random_forest"] = "lineal"
    imputar: bool = False
    test_size: float = Field(0.2, ge=0.1, le=0.4)


class ConsumoRealEntrada(BaseModel):
    id_prediccion: int = Field(..., ge=1)
    consumo_real: float = Field(..., ge=0, le=1000)


class ChatEntrada(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=2000)
    historial: List[dict] = Field(default_factory=list)
