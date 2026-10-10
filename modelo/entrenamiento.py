"""Modulo de entrenamiento de modelos de Machine Learning para ElectroPredict.

Soporta varios algoritmos de regresion (Regresion Lineal Multiple, Ridge y
Random Forest) mediante scikit-learn. La imputacion de valores faltantes,
cuando se habilita, se ajusta UNICAMENTE con los datos de entrenamiento para
evitar fuga de informacion.
"""

import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any, List

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer

from datos.validaciones import (
    validar_personas,
    validar_temperatura,
    validar_horas_uso,
    validar_consumo,
    validar_consumo_anterior,
)

logger = logging.getLogger(__name__)

# Algoritmos soportados: clave -> nombre legible
ALGORITMOS: Dict[str, str] = {
    "lineal": "Regresion Lineal Multiple",
    "ridge": "Regresion Ridge (L2)",
    "random_forest": "Random Forest",
}


class ModeloRegresionLineal:
    """Modelo de regresion para prediccion de consumo electrico.

    Aunque conserva el nombre por compatibilidad, soporta varios algoritmos.
    """

    def __init__(self, algoritmo: str = "lineal", imputar: bool = False) -> None:
        if algoritmo not in ALGORITMOS:
            raise ValueError(f"Algoritmo no soportado: {algoritmo}")
        self._algoritmo = algoritmo
        self._imputar = bool(imputar)
        self._imputador: Optional[SimpleImputer] = None
        self._modelo = self._crear_estimador(algoritmo)
        self._coeficientes: Optional[np.ndarray] = None
        self._intercepto: Optional[float] = None
        self._feature_names: List[str] = [
            "temperatura", "personas", "horas_uso", "consumo_anterior"
        ]
        self._entrenado = False
        self._metricas: Optional[Dict[str, float]] = None
        self._version = "1.1.0"
        self._X_test: Optional[np.ndarray] = None
        self._y_test: Optional[np.ndarray] = None
        self._X_train: Optional[np.ndarray] = None
        self._y_train: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------
    @staticmethod
    def _crear_estimador(algoritmo: str):
        if algoritmo == "lineal":
            return LinearRegression()
        if algoritmo == "ridge":
            return Ridge(alpha=1.0, random_state=42)
        if algoritmo == "random_forest":
            return RandomForestRegressor(n_estimators=200, random_state=42)
        raise ValueError(f"Algoritmo no soportado: {algoritmo}")

    @property
    def entrenado(self) -> bool:
        return self._entrenado

    @property
    def algoritmo(self) -> str:
        return self._algoritmo

    @property
    def algoritmo_nombre(self) -> str:
        return ALGORITMOS.get(self._algoritmo, self._algoritmo)

    @property
    def imputar(self) -> bool:
        return self._imputar

    @property
    def version(self) -> str:
        return self._version

    @property
    def coeficientes(self) -> Optional[np.ndarray]:
        return self._coeficientes

    @property
    def intercepto(self) -> Optional[float]:
        return self._intercepto

    @property
    def feature_names(self) -> List[str]:
        return list(self._feature_names)

    @property
    def metricas(self) -> Optional[Dict[str, float]]:
        return self._metricas

    @property
    def datos_prueba(self):
        """Devuelve (X_test, y_test) utilizados en la evaluacion."""
        return self._X_test, self._y_test

    @property
    def n_entrenamiento(self) -> int:
        return 0 if self._X_train is None else len(self._X_train)

    @property
    def n_prueba(self) -> int:
        return 0 if self._X_test is None else len(self._X_test)

    # ------------------------------------------------------------------
    # Preparacion de datos
    # ------------------------------------------------------------------
    def preparar_datos(
        self,
        datos: List[Dict[str, Any]],
        permitir_faltantes: Optional[bool] = None,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Separa caracteristicas y objetivo.

        Si ``permitir_faltantes`` es True, los valores de entrada invalidos o
        vacios se convierten en ``np.nan`` para que el imputador los complete
        (el objetivo nunca puede faltar: esas filas se descartan).
        """
        if permitir_faltantes is None:
            permitir_faltantes = self._imputar

        if not datos:
            logger.warning("No hay datos para preparar")
            return None, None

        validadores = {
            "temperatura": validar_temperatura,
            "personas": validar_personas,
            "horas_uso": validar_horas_uso,
            "consumo_anterior": validar_consumo_anterior,
        }

        X: List[List[float]] = []
        y: List[float] = []

        for fila in datos:
            valores = []
            valido = True
            for col in self._feature_names:
                valor, err = validadores[col](str(fila.get(col, "")))
                if err:
                    if permitir_faltantes:
                        valores.append(np.nan)
                    else:
                        logger.warning(f"Dato invalido en '{col}': {err}")
                        return None, None
                else:
                    valores.append(float(valor))

            con_real, err_real = validar_consumo(str(fila.get("consumo_real", "")))
            if err_real:
                if permitir_faltantes:
                    # El objetivo no puede imputarse con sentido: se descarta la fila
                    continue
                logger.warning(f"Dato invalido en objetivo: {err_real}")
                return None, None

            X.append(valores)
            y.append(float(con_real))

        if len(X) < 3:
            logger.warning("Insuficientes datos validos para entrenamiento (minimo 3)")
            return None, None

        return np.array(X, dtype=float), np.array(y, dtype=float)

    # ------------------------------------------------------------------
    # Entrenamiento
    # ------------------------------------------------------------------
    def entrenar(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict[str, Any]:
        """Entrena el modelo con division entrenamiento/prueba."""

        if X is None or y is None or len(X) < 3:
            return {"exitoso": False, "error": "Datos insuficientes", "metricas": None}

        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        try:
            # Si no hay faltantes, la division es directa; si los hay y la
            # imputacion esta deshabilitada, se rechazan.
            if not self._imputar and np.isnan(X).any():
                return {
                    "exitoso": False,
                    "error": "Hay valores faltantes. Habilite la imputacion o limpie los datos.",
                    "metricas": None,
                }

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Imputacion ajustada SOLO con el conjunto de entrenamiento
            if self._imputar:
                self._imputador = SimpleImputer(strategy="mean")
                X_train = self._imputador.fit_transform(X_train)
                X_test = self._imputador.transform(X_test)

            self._modelo.fit(X_train, y_train)

            self._X_train, self._y_train = X_train, y_train
            self._X_test, self._y_test = X_test, y_test
            self._entrenado = True
            self._extraer_parametros()

            y_pred = self._modelo.predict(X_test)
            self._metricas = {
                "r2": float(r2_score(y_test, y_pred)),
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "mse": float(mean_squared_error(y_test, y_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            }

            resultado = {
                "exitoso": True,
                "algoritmo": self._algoritmo,
                "algoritmo_nombre": self.algoritmo_nombre,
                "imputacion": self._imputar,
                "num_registros": len(X),
                "registros_entrenamiento": len(X_train),
                "registros_prueba": len(X_test),
                "metricas": self._metricas,
                "coeficientes": (
                    dict(zip(self._feature_names, self._coeficientes))
                    if self._coeficientes is not None else {}
                ),
                "intercepto": self._intercepto,
                "version": self._version,
            }
            logger.info(
                f"Modelo '{self._algoritmo}' entrenado. R2={self._metricas['r2']:.4f}")
            return resultado

        except Exception as e:
            self._entrenado = False
            logger.error(f"Error entrenando modelo: {e}")
            return {"exitoso": False, "error": str(e), "metricas": None}

    def _extraer_parametros(self) -> None:
        """Extrae coeficientes/intercepto solo si el estimador los expone."""
        if hasattr(self._modelo, "coef_"):
            self._coeficientes = np.ravel(self._modelo.coef_)
        else:
            self._coeficientes = None
        if hasattr(self._modelo, "intercept_"):
            self._intercepto = float(np.ravel(self._modelo.intercept_)[0])
        else:
            self._intercepto = None

    # ------------------------------------------------------------------
    # Prediccion
    # ------------------------------------------------------------------
    def predecir(self, datos_entrada: List[float]) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
        """Predice un unico registro validando las entradas."""
        if not self._entrenado:
            logger.error("Intento de prediccion con modelo sin entrenar")
            return None, None

        validadores = [
            validar_temperatura, validar_personas,
            validar_horas_uso, validar_consumo_anterior,
        ]
        valores = []
        for i, validador in enumerate(validadores):
            valor, err = validador(str(datos_entrada[i]))
            if err:
                logger.error(f"Entrada invalida: {err}")
                return None, None
            valores.append(float(valor))

        try:
            entrada = np.array([valores], dtype=float)
            if self._imputar and self._imputador is not None:
                entrada = self._imputador.transform(entrada)
            consumo = float(np.ravel(self._modelo.predict(entrada))[0])
        except Exception as e:
            logger.error(f"Error realizando prediccion: {e}")
            return None, None

        info = {
            "algoritmo": self._algoritmo,
            "coeficientes": (
                dict(zip(self._feature_names, self._coeficientes))
                if self._coeficientes is not None else {}),
            "intercepto": self._intercepto,
        }
        return consumo, info

    def predecir_array(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Predice un arreglo (usado internamente para evaluacion/graficas)."""
        if not self._entrenado:
            return None
        X = np.asarray(X, dtype=float)
        if self._imputar and self._imputador is not None:
            X = self._imputador.transform(X)
        return np.asarray(self._modelo.predict(X), dtype=float)

    # ------------------------------------------------------------------
    # Presentacion
    # ------------------------------------------------------------------
    def obtener_formula(self) -> str:
        if not self._entrenado:
            return "Modelo no entrenado"
        if self._coeficientes is None:
            return (f"El algoritmo '{self.algoritmo_nombre}' no expone una ecuacion "
                    f"lineal de coeficientes.")
        nombres = self._feature_names
        partes = [f"b0 = {self._intercepto:.4f}"]
        terminos = []
        for i, coef in enumerate(self._coeficientes, start=1):
            terminos.append(f"{coef:.4f}*{nombres[i - 1]}")
        formula = f"consumo_estimado = b0 + {' + '.join(terminos)}"
        return f"{formula}\nDonde: {', '.join(partes)}"


def comparar_algoritmos(
    datos: List[Dict[str, Any]],
    algoritmo_1: str = "lineal",
    test_size: float = 0.2,
    imputar: bool = False,
) -> List[Dict[str, Any]]:
    """Entrena varios algoritmos con los mismos datos y devuelve sus metricas.

    Returns:
        Lista de diccionarios con 'algoritmo', 'nombre', 'metricas' y 'exitoso'.
    """
    resultados = []
    for clave in ALGORITMOS:
        modelo = ModeloRegresionLineal(algoritmo=clave, imputar=imputar)
        X, y = modelo.preparar_datos(datos)
        if X is None or y is None:
            resultados.append({"algoritmo": clave, "nombre": ALGORITMOS[clave],
                               "exitoso": False, "metricas": None})
            continue
        res = modelo.entrenar(X, y, test_size=test_size)
        resultados.append({
            "algoritmo": clave,
            "nombre": ALGORITMOS[clave],
            "exitoso": res.get("exitoso", False),
            "metricas": res.get("metricas"),
        })
    return resultados
