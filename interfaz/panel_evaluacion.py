"""Panel de Evaluacion del modelo de ElectroPredict.

Reune las visualizaciones calculadas con datos reales:
real vs predicho, dispersion, errores, distribucion, historico,
historial de predicciones y resultados por lotes.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from interfaz import tema
from interfaz.componentes import limpiar_frame
from modelo.evaluacion import evaluar_modelo
from graficas import visualizaciones

logger = logging.getLogger(__name__)


class PanelEvaluacion(ttk.Frame):
    """Evaluacion estadistica y visual del rendimiento del modelo."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._canvas: list = []
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        barra = ttk.Frame(self, style="TFrame")
        barra.pack(fill="x", pady=(0, 10))
        ttk.Button(barra, text="Recalcular evaluacion", style="Primario.TButton",
                   command=self.refrescar).pack(side="left")
        self._lbl_metricas = ttk.Label(barra, text="", style="TLabel")
        self._lbl_metricas.pack(side="left", padx=16)

        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)

        titulos = [
            "Real vs predicho", "Dispersion", "Errores", "Distribucion",
            "Historico", "Predicciones", "Lotes",
        ]
        self._tabs = {}
        for titulo in titulos:
            frame = ttk.Frame(self._notebook, style="TFrame")
            self._notebook.add(frame, text=titulo)
            self._tabs[titulo] = frame

    # ------------------------------------------------------------------
    def _limpiar(self) -> None:
        for c in self._canvas:
            try:
                c.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvas = []
        for frame in self._tabs.values():
            limpiar_frame(frame)

    def _embeber(self, figura, contenedor) -> None:
        if figura is None:
            ttk.Label(contenedor, text="No hay datos suficientes para esta grafica.",
                      style="Suave.TLabel").pack(pady=20)
            return
        canvas = FigureCanvasTkAgg(figura, master=contenedor)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._canvas.append(canvas)

    def _datos_test(self) -> Tuple[List[float], List[float]]:
        """Devuelve (y_real, y_pred) del conjunto de prueba del modelo."""
        if not self.app.modelo.entrenado:
            return [], []
        X_test, y_test = self.app.modelo.datos_prueba
        if X_test is None or y_test is None or len(X_test) == 0:
            return [], []
        y_pred = self.app.modelo.predecir_array(X_test)
        if y_pred is None:
            return [], []
        return list(y_test), [float(v) for v in y_pred]

    def _datos_historial(self):
        """Predicciones con consumo real conocido."""
        reales, predichos = [], []
        for p in self.app.gestor.predicciones():
            if p.get("consumo_real") is not None:
                reales.append(p["consumo_real"])
                predichos.append(p["consumo_estimado"])
        return reales, predichos

    def refrescar(self) -> None:
        self._limpiar()
        visualizador = self.app.visualizador

        if not self.app.modelo.entrenado:
            self._lbl_metricas.configure(
                text="El modelo no esta entrenado. Entrenelo para ver la evaluacion.",
                foreground=tema.COLOR_ADVERTENCIA)
            for frame in self._tabs.values():
                ttk.Label(frame, style="Suave.TLabel",
                          text="No hay modelo entrenado.").pack(pady=20)
            return

        # Metricas actuales
        y_real, y_pred = self._datos_test()
        metricas = self.app.metricas or {}
        self._lbl_metricas.configure(
            text=(f"R2={metricas.get('r2', 0):.4f}   MAE={metricas.get('mae', 0):.4f}   "
                  f"MSE={metricas.get('mse', 0):.4f}   RMSE={metricas.get('rmse', 0):.4f}"),
            foreground=tema.COLOR_TEXTO,
        )

        # 1. Real vs predicho (conjunto de prueba)
        fig = visualizador.crear_grafico_consumo_real_predicho(
            y_real, y_pred, "Consumo real vs predicho (conjunto de prueba)")
        self._embeber(fig, self._tabs["Real vs predicho"])

        # 2. Dispersion temperatura vs consumo
        registros = self.app.gestor.registros()
        temperaturas = [r["temperatura"] for r in registros]
        consumos = [r["consumo_real"] for r in registros]
        fig = visualizador.crear_grafico_dispersion(
            temperaturas, consumos, None, "Temperatura vs consumo real")
        self._embeber(fig, self._tabs["Dispersion"])

        # 3. Errores de prediccion (test)
        fig = visualizador.crear_grafico_errores(y_real, y_pred)
        self._embeber(fig, self._tabs["Errores"])

        # 4. Distribucion de errores
        fig = visualizador.crear_grafico_distribucion_errores(y_real, y_pred)
        self._embeber(fig, self._tabs["Distribucion"])

        # 5. Evolucion historica
        fechas = [r.get("fecha_registro", str(i + 1)) for i, r in enumerate(registros)]
        fig = visualizador.crear_grafico_evolucion_historico(
            fechas, consumos, "Evolucion del consumo historico")
        self._embeber(fig, self._tabs["Historico"])

        # 6. Historial de predicciones
        predicciones = self.app.gestor.predicciones()
        if predicciones:
            fechas_p = [p["fecha"] for p in predicciones]
            estimados = [p["consumo_estimado"] for p in predicciones]
            reales = [p.get("consumo_real") for p in predicciones]
            reales_validos = reales if all(r is not None for r in reales) else None
            fig = visualizador.crear_grafico_historial_predicciones(
                fechas_p, estimados, reales_validos, "Historial de predicciones")
        else:
            fig = None
        self._embeber(fig, self._tabs["Predicciones"])

        # 7. Resultados por lotes
        lote = [p for p in predicciones if p.get("tipo") == "lote"]
        if lote:
            filas = list(range(1, len(lote) + 1))
            estimados = [p["consumo_estimado"] for p in lote]
            reales = [p.get("consumo_real") for p in lote]
            reales_validos = reales if all(r is not None for r in reales) else None
            fig = visualizador.crear_grafico_resultados_lotes(
                filas, estimados, reales_validos, "Resultados del ultimo lote")
        else:
            fig = None
        self._embeber(fig, self._tabs["Lotes"])
