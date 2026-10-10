"""Panel de Prediccion individual de ElectroPredict."""

import logging
import tkinter as tk
from tkinter import ttk

from interfaz import tema
from datos.validaciones import (
    validar_temperatura, validar_personas, validar_horas_uso, validar_consumo_anterior,
    validar_consumo,
)

logger = logging.getLogger(__name__)


class PanelPrediccion(ttk.Frame):
    """Formulario para predecir el consumo a partir de cuatro variables."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._ultima_prediccion = None
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        ttk.Label(
            self, style="TLabel", wraplength=820, justify="left",
            text=("Ingrese los valores de las cuatro variables de entrada. "
                  "El modelo entrenado calculara el consumo estimado en kWh."),
        ).pack(anchor="w", pady=(0, 14))

        self._lbl_estado_modelo = ttk.Label(self, text="", style="TLabel")
        self._lbl_estado_modelo.pack(anchor="w", pady=(0, 10))

        contenedor = ttk.Frame(self, style="TFrame")
        contenedor.pack(anchor="w")

        self._campos = {}
        definiciones = [
            ("temperatura", "Temperatura (C)", "-50 a 60"),
            ("personas", "Cantidad de personas", "1 a 50"),
            ("horas_uso", "Horas de uso de equipos", "0 a 24"),
            ("consumo_anterior", "Consumo del dia anterior (kWh)", "0 a 1000"),
        ]
        for i, (clave, etiqueta, ayuda) in enumerate(definiciones):
            ttk.Label(contenedor, text=etiqueta, style="TLabel").grid(
                row=i, column=0, sticky="w", pady=7, padx=(0, 12))
            entry = ttk.Entry(contenedor, width=22)
            entry.grid(row=i, column=1, sticky="w", pady=7)
            ttk.Label(contenedor, text=ayuda, style="Suave.TLabel").grid(
                row=i, column=2, sticky="w", padx=(12, 0), pady=7)
            self._campos[clave] = entry

        # Campo opcional consumo real
        ttk.Label(contenedor, text="Consumo real, si se conoce (kWh)", style="TLabel").grid(
            row=4, column=0, sticky="w", pady=7, padx=(0, 12))
        self._campo_real = ttk.Entry(contenedor, width=22)
        self._campo_real.grid(row=4, column=1, sticky="w", pady=7)
        ttk.Label(contenedor, text="opcional, para calcular error", style="Suave.TLabel").grid(
            row=4, column=2, sticky="w", padx=(12, 0), pady=7)

        botones = ttk.Frame(self, style="TFrame")
        botones.pack(anchor="w", pady=(16, 8))
        ttk.Button(botones, text="Predecir consumo", style="Primario.TButton",
                   command=self._predecir).pack(side="left")
        self._btn_guardar = ttk.Button(botones, text="Guardar prediccion",
                                       command=self._guardar, state="disabled")
        self._btn_guardar.pack(side="left", padx=8)

        self._lbl_error = ttk.Label(self, text="", style="Error.TLabel", wraplength=700)
        self._lbl_error.pack(anchor="w")

        self._lbl_resultado = ttk.Label(self, text="", style="Titulo.TLabel")
        self._lbl_resultado.pack(anchor="w", pady=(14, 0))
        self._lbl_detalle = ttk.Label(self, text="", style="Suave.TLabel")
        self._lbl_detalle.pack(anchor="w")

    def refrescar(self) -> None:
        if self.app.modelo.entrenado:
            r2 = (self.app.metricas or {}).get("r2")
            extra = f"  R2 = {r2:.3f}" if r2 is not None else ""
            self._lbl_estado_modelo.configure(
                text=f"Modelo listo para predecir.{extra}", foreground=tema.COLOR_EXITO)
        else:
            self._lbl_estado_modelo.configure(
                text="El modelo no esta entrenado. Vaya a 'Entrenamiento' primero.",
                foreground=tema.COLOR_ADVERTENCIA)

    def _predecir(self) -> None:
        self._lbl_error.configure(text="")
        self._lbl_resultado.configure(text="")
        self._lbl_detalle.configure(text="")
        self._btn_guardar.configure(state="disabled")
        self._ultima_prediccion = None

        if not self.app.modelo.entrenado:
            self._lbl_error.configure(text="No hay un modelo entrenado. Entrene el modelo primero.")
            return

        validadores = {
            "temperatura": validar_temperatura,
            "personas": validar_personas,
            "horas_uso": validar_horas_uso,
            "consumo_anterior": validar_consumo_anterior,
        }
        valores = {}
        for clave, validador in validadores.items():
            val, err = validador(self._campos[clave].get())
            if err:
                self._lbl_error.configure(text=err)
                return
            valores[clave] = val

        consumo_real = None
        texto_real = self._campo_real.get().strip()
        if texto_real:
            consumo_real, err = validar_consumo(texto_real)
            if err:
                self._lbl_error.configure(text=err)
                return

        estimado, info = self.app.modelo.predecir([
            valores["temperatura"], valores["personas"],
            valores["horas_uso"], valores["consumo_anterior"],
        ])
        if estimado is None:
            self._lbl_error.configure(text="No se pudo realizar la prediccion.")
            return

        self._lbl_resultado.configure(text=f"Consumo estimado: {estimado:.2f} kWh")

        detalle = ""
        if consumo_real is not None:
            error = consumo_real - estimado
            detalle = (f"Consumo real: {consumo_real:.2f} kWh   |   "
                       f"Error = real - estimado = {error:.2f} kWh   |   "
                       f"Error absoluto = {abs(error):.2f} kWh")
        self._lbl_detalle.configure(text=detalle)

        self._ultima_prediccion = {
            "valores": valores,
            "estimado": estimado,
            "consumo_real": consumo_real,
        }
        self._btn_guardar.configure(state="normal")

    def _guardar(self) -> None:
        if not self._ultima_prediccion:
            return
        v = self._ultima_prediccion["valores"]
        self.app.gestor.agregar_prediccion(
            v["temperatura"], v["personas"], v["horas_uso"], v["consumo_anterior"],
            self._ultima_prediccion["estimado"],
            modelo=f"v{self.app.modelo.version}",
            tipo="individual",
            consumo_real=self._ultima_prediccion["consumo_real"],
        )
        self.app.actualizar_todo()
        self.app.mostrar_mensaje("Prediccion guardada",
                                 "La prediccion se registro en el historial.", "success")
