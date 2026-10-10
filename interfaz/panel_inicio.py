"""Panel de Inicio (Dashboard) de ElectroPredict."""

import logging
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from interfaz import tema
from interfaz.componentes import crear_tarjeta, limpiar_frame

logger = logging.getLogger(__name__)


class PanelInicio(ttk.Frame):
    """Dashboard principal con tarjetas estadisticas y graficas resumidas."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._canvas: list = []
        self._construir()

    def _construir(self) -> None:
        self._tarjetas_frame = ttk.Frame(self, style="TFrame")
        self._tarjetas_frame.pack(fill="x")

        self._mensaje_vacio = ttk.Label(
            self, text="", style="TLabel", justify="left",
        )

        self._cuerpo = ttk.Frame(self, style="TFrame")
        self._cuerpo.pack(fill="both", expand=True, pady=(20, 0))

        self._crear_tarjetas()
        self._graficas_frame = ttk.Frame(self._cuerpo, style="TFrame")
        self._graficas_frame.pack(fill="both", expand=True)

        self.refrescar()

    def _crear_tarjetas(self) -> None:
        for w in self._tarjetas_frame.winfo_children():
            w.destroy()

        especificaciones = [
            ("Registros historicos", "registros"),
            ("Ultimo consumo", "ultimo"),
            ("Predicciones", "predicciones"),
            ("Estado del modelo", "modelo"),
        ]
        self._valores: dict = {}
        for i, (titulo, clave) in enumerate(especificaciones):
            tarjeta, lbl = crear_tarjeta(self._tarjetas_frame, titulo)
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0), pady=4)
            self._tarjetas_frame.columnconfigure(i, weight=1)
            self._valores[clave] = lbl

        self._fecha_entreno = ttk.Label(self._tarjetas_frame, text="", style="Suave.TLabel")

    def refrescar(self) -> None:
        gestor = self.app.gestor
        num_registros = gestor.cantidad_registros()
        num_pred = gestor.cantidad_predicciones()
        ultimo = gestor.ultimo_consumo()

        self._valores["registros"].configure(text=f"{num_registros}")
        if ultimo:
            self._valores["ultimo"].configure(
                text=f"{ultimo['consumo_real']:.2f} kWh")
        else:
            self._valores["ultimo"].configure(text="--")
        self._valores["predicciones"].configure(text=f"{num_pred}")

        if self.app.modelo.entrenado and self.app.metricas:
            r2 = self.app.metricas.get("r2")
            self._valores["modelo"].configure(
                text=f"R2 {r2:.3f}" if r2 is not None else "Entrenado")
        else:
            self._valores["modelo"].configure(text="No entrenado")

        self._actualizar_graficas()

    # ------------------------------------------------------------------
    def _actualizar_graficas(self) -> None:
        limpiar_frame(self._graficas_frame)
        for c in self._canvas:
            try:
                c.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvas = []

        gestor = self.app.gestor
        registros = gestor.registros()
        predicciones = gestor.predicciones()

        if not registros:
            self._mostrar_estado_vacio()
            return

        self._mensaje_vacio.pack_forget()

        # Grafica 1: evolucion historica
        frame_izq = ttk.Frame(self._graficas_frame, style="TFrame")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frame_der = ttk.Frame(self._graficas_frame, style="TFrame")
        frame_der.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._graficas_frame.columnconfigure(0, weight=1)
        self._graficas_frame.columnconfigure(1, weight=1)
        self._graficas_frame.rowconfigure(0, weight=1)

        # Consumo historico
        fig1 = Figure(figsize=(5, 3.2), dpi=90)
        ax1 = fig1.add_subplot(111)
        consumos = [r["consumo_real"] for r in registros]
        ax1.plot(range(1, len(consumos) + 1), consumos, marker="o",
                 color=tema.COLOR_PRIMARIO, linewidth=1.6)
        ax1.set_title("Consumo historico (kWh)", fontsize=10)
        ax1.set_xlabel("Registro", fontsize=9)
        ax1.set_ylabel("kWh", fontsize=9)
        ax1.grid(True, alpha=0.3)
        fig1.tight_layout()
        self._embeber(fig1, frame_izq)

        # Predicciones recientes
        fig2 = Figure(figsize=(5, 3.2), dpi=90)
        ax2 = fig2.add_subplot(111)
        if predicciones:
            ultimas = predicciones[-12:]
            valores = [p["consumo_estimado"] for p in ultimas]
            ax2.bar(range(1, len(valores) + 1), valores, color=tema.COLOR_EXITO)
            ax2.set_title("Predicciones recientes (kWh)", fontsize=10)
            ax2.set_xlabel("Prediccion", fontsize=9)
            ax2.set_ylabel("kWh", fontsize=9)
        else:
            ax2.text(0.5, 0.5, "Aun no hay predicciones registradas",
                     ha="center", va="center", fontsize=10, color="#6b7280")
            ax2.set_axis_off()
        ax2.grid(True, alpha=0.3)
        fig2.tight_layout()
        self._embeber(fig2, frame_der)

    def _embeber(self, figura, contenedor) -> None:
        canvas = FigureCanvasTkAgg(figura, master=contenedor)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas.append(canvas)

    def _mostrar_estado_vacio(self) -> None:
        self._mensaje_vacio.configure(
            text=(
                "Todavia no hay datos historicos.\n\n"
                "Para comenzar:\n"
                "   1. Ve a 'Datos historicos' e importa un CSV o registra datos manuales.\n"
                "   2. Entrena el modelo en la seccion 'Entrenamiento'.\n"
                "   3. Realiza predicciones individuales o por lotes.\n\n"
                "Las estadisticas y graficas apareceran cuando existan datos reales."
            )
        )
        self._mensaje_vacio.pack(fill="x", pady=(30, 0))
