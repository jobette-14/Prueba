"""Módulo de visualizaciones para ElectroPredict.

Utiliza Matplotlib para generar gráficas integradas en la interfaz Tkinter."""
import logging
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class VisualizadorGraficas:
    """Clase para crear y gestionar gráficas en la interfaz Tkinter."""

    def __init__(self, padre=None) -> None:
        self._padre = padre
        self._figuras: List[Figure] = []
        self._canvas_list: List[FigureCanvasTkAgg] = []

    def crear_grafico_consumo_real_predicho(
        self,
        consumos_reales: List[float],
        consumos_predichos: List[float],
        titulo: str = "Consumo Real vs Predicho",
    ) -> Optional[Figure]:
        """Crea un gráfico de dispersión comparando consumo real vs predicho.

        Args:
            consumos_reales: Lista de valores de consumo real.
            consumos_predichos: Lista de valores de consumo predicho.
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not consumos_reales or not consumos_predichos:
            logger.warning("No hay datos para graficar consumo real vs predicho")
            return None

        if len(consumos_reales) != len(consumos_predichos):
            logger.error("Las listas deben tener la misma longitud")
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Graficar puntos
            ax.scatter(consumos_reales, consumos_predichos, color='blue', alpha=0.7, label='Datos')

            # Línea de referencia perfecta (y = x)
            min_val = min(min(consumos_reales), min(consumos_predichos))
            max_val = max(max(consumos_reales), max(consumos_predichos))
            ax.plot([min_val, max_val], [min_val, max_val], color='red', linestyle='--', label='Perfecto ajuste')

            ax.set_xlabel('Consumo real (kWh)')
            ax.set_ylabel('Consumo predicho (kWh)')
            ax.set_title(titulo)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal', adjustable='box')

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando gráfico consumo real vs predicho: {e}")
            return None

    def crear_grafico_dispersion(
        self,
        temperatura: List[float],
        consumo_real: List[float],
        consumo_predicho: Optional[List[float]] = None,
        titulo: str = "Dispersión: Temperatura vs Consumo",
    ) -> Optional[Figure]:
        """Crea un gráfico de dispersión entre temperatura y consumo.

        Args:
            temperatura: Lista de valores de temperatura.
            consumo_real: Lista de valores de consumo real.
            consumo_predicho: Lista opcional de valores predichos.
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not temperatura or not consumo_real:
            logger.warning("No hay datos para gráfico de dispersión")
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Graficar consumo real
            ax.scatter(temperatura, consumo_real, color='blue', alpha=0.7, label='Real', s=50)

            # Si hay predichos, mostrarlos también
            if consumo_predicho and len(consumo_predicho) == len(temperatura):
                ax.scatter(temperatura, consumo_predicho, color='red', alpha=0.5, label='Predicho', s=50, marker='x')

            ax.set_xlabel('Temperatura (°C)')
            ax.set_ylabel('Consumo (kWh)')
            ax.set_title(titulo)
            ax.legend()
            ax.grid(True, alpha=0.3)

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando gráfico dispersión: {e}")
            return None

    def crear_grafico_errores(
        self,
        consumos_reales: List[float],
        consumos_predichos: List[float],
        titulo: str = "Errores de Predicción",
    ) -> Optional[Figure]:
        """Crea un gráfico de errores de predicción.

        Args:
            consumos_reales: Valores reales.
            consumos_predichos: Valores predichos.
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not consumos_reales or not consumos_predichos:
            logger.warning("No hay datos para gráfico de errores")
            return None

        if len(consumos_reales) != len(consumos_predichos):
            logger.error("Las listas deben tener la misma longitud")
            return None

        try:
            # Calcular errores
            errores = [real - predicho for real, predicho in zip(consumos_reales, consumos_predichos)]
            error_absoluto = [abs(e) for e in errores]

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

            # Gráfico de errores
            ax1.plot(errores, color='orange', marker='o', linestyle='-')
            ax1.axhline(y=0, color='red', linestyle='--')
            ax1.set_ylabel('Error (kWh)')
            ax1.set_title(titulo)
            ax1.grid(True, alpha=0.3)

            # Gráfico de error absoluto
            ax2.plot(error_absoluto, color='green', marker='s', linestyle='-')
            ax2.set_xlabel('Índice de predicción')
            ax2.set_ylabel('Error absoluto (kWh)')
            ax2.set_title('Error Absoluto de Predicción')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando gráfico de errores: {e}")
            return None

    def crear_grafico_distribucion_errores(
        self,
        consumos_reales: List[float],
        consumos_predichos: List[float],
        titulo: str = "Distribución de Errores",
    ) -> Optional[Figure]:
        """Crea un histograma de la distribución de errores.

        Args:
            consumos_reales: Valores reales.
            consumos_predichos: Valores predichos.
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not consumos_reales or not consumos_predichos:
            logger.warning("No hay datos para distribución de errores")
            return None

        try:
            # Calcular errores
            errores = [real - predicho for real, predicho in zip(consumos_reales, consumos_predichos)]

            fig, ax = plt.subplots(figsize=(10, 6))

            ax.hist(errores, bins='auto', color='steelblue', edgecolor='white', alpha=0.7)
            ax.axvline(x=0, color='red', linestyle='--', linewidth=2)

            ax.set_xlabel('Error (Consumo real - Consumo predicho) [kWh]')
            ax.set_ylabel('Frecuencia')
            ax.set_title(titulo)
            ax.grid(True, alpha=0.3)

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando distribución de errores: {e}")
            return None

    def crear_grafico_evolucion_historico(
        self,
        fechas: List[str],
        consumos: List[float],
        titulo: str = "Evolución Histórica del Consumo",
    ) -> Optional[Figure]:
        """Crea un gráfico de línea de la evolución histórica del consumo.

        Args:
            fechas: Lista de fechas (strings formateados).
            consumos: Lista de valores de consumo.
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not fechas or not consumos:
            logger.warning("No hay datos para gráfico de evolución histórica")
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Convertir fechas si es posible
            try:
                fechas_parseadas = [f if hasattr(f, 'strftime') else str(f) for f in fechas]
                ax.plot(fechas_parseadas, consumos, marker='o', linestyle='-', color='darkgreen')
            except Exception:
                # Si no se pueden parsear, usar índices
                ax.plot(consumos, marker='o', linestyle='-', color='darkgreen')
                ax.set_xticks(range(len(fechas)))
                ax.set_xticklabels([str(f) for f in fechas], rotation=45, ha='right')

            ax.set_xlabel('Fecha')
            ax.set_ylabel('Consumo (kWh)')
            ax.set_title(titulo)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando gráfico evolución histórica: {e}")
            return None

    def crear_grafico_historial_predicciones(
        self,
        fechas: List[str],
        consumos_estimados: List[float],
        consumos_reales: Optional[List[float]] = None,
        titulo: str = "Historial de Predicciones",
    ) -> Optional[Figure]:
        """Crea un gráfico del historial de predicciones.

        Args:
            fechas: Lista de fechas de las predicciones.
            consumos_estimados: Lista de consumos estimados.
            consumos_reales: Lista opcional de consumos reales (para comparar).
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not fechas or not consumos_estimados:
            logger.warning("No hay datos para historial de predicciones")
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Graficar estimados
            ax.plot(fechas, consumos_estimados, marker='o', linestyle='-', color='blue', label='Estimado')

            # Si hay reales, mostrarlos también
            if consumos_reales and len(consumos_reales) == len(consumos_estimados):
                ax.plot(fechas, consumos_reales, marker='s', linestyle='--', color='red', label='Real')

            ax.set_xlabel('Fecha')
            ax.set_ylabel('Consumo (kWh)')
            ax.set_title(titulo)
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando historial de predicciones: {e}")
            return None

    def crear_grafico_resultados_lotes(
        self,
        filas: List[int],
        consumos_estimados: List[float],
        consumos_reales: Optional[List[float]] = None,
        titulo: str = "Resultados por Lotes",
    ) -> Optional[Figure]:
        """Crea un gráfico de resultados de predicciones por lotes.

        Args:
            filas: Lista de números de fila/índice.
            consumos_estimados: Lista de consumos estimados.
            consumos_reales: Lista opcional de consumos reales.
            titulo: Título de la gráfica.

        Returns:
            Figura de Matplotlib o None si hay error.
        """
        if not filas or not consumos_estimados:
            logger.warning("No hay datos para gráfico de resultados por lotes")
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Graficar estimados
            ax.plot(filas, consumos_estimados, marker='o', linestyle='-', color='blue', label='Estimado')

            # Si hay reales, mostrarlos también
            if consumos_reales and len(consumos_reales) == len(consumos_estimados):
                ax.plot(filas, consumos_reales, marker='s', linestyle='--', color='red', label='Real')

            ax.set_xlabel('Fila / Índice')
            ax.set_ylabel('Consumo (kWh)')
            ax.set_title(titulo)
            ax.legend()
            ax.grid(True, alpha=0.3)

            self._figuras.append(fig)
            return fig

        except Exception as e:
            logger.error(f"Error creando gráfico resultados por lotes: {e}")
            return None

    def dibujar_en_contenedor(
        self,
        figura: Figure,
        contenedor,
        pad_izquierdo: int = 10,
        pad_superior: int = 10,
    ) -> Optional[FigureCanvasTkAgg]:
        """Dibuja una figura de Matplotlib en un contenedor Tkinter.

        Args:
            figura: Figura de Matplotlib a dibujar.
            contenedor: Contenedor Tkinter (frame o ventana).
            pad_izquierdo: Margen horizontal.
            pad_superior: Margen vertical.

        Returns:
            Canvas de Tkinter con la grafica integrado.
        """
        try:
            canvas = FigureCanvasTkAgg(figura, master=contenedor)
            canvas.draw()
            canvas.get_tk_widget().pack(
                fill="both",
                expand=True,
                padx=pad_izquierdo,
                pady=pad_superior,
            )
            self._canvas_list.append(canvas)
            return canvas
        except Exception as e:
            logger.error(f"Error dibujando grafica en contenedor: {e}")
            return None

    def limpiar_graficas(self) -> None:
        """Limpia todas las figuras y canales creados."""
        for fig in self._figuras:
            plt.close(fig)
        self._figuras = []
        self._canvas_list = []