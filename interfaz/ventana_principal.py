"""Ventana principal de ElectroPredict.

Contiene el menu lateral, el encabezado, el area de contenido con todas
las secciones y la barra de estado. Coordina el estado compartido entre
paneles a traves del objeto de aplicacion.
"""

import threading
import logging
import os
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any

from interfaz import tema
from interfaz.componentes import BarraEstado, mostrar_mensaje
from interfaz.tema import Tema

from datos.gestor import GestorDatos
from modelo.entrenamiento import ModeloRegresionLineal
from base_datos.conexion import ConexionPostgreSQL
from base_datos.repositorio import RepositorioPostgreSQL
from graficas.visualizaciones import VisualizadorGraficas

logger = logging.getLogger(__name__)


SECCIONES = [
    ("inicio", "Inicio", "\U0001F3E0"),
    ("datos", "Datos historicos", "\U0001F4C4"),
    ("entrenamiento", "Entrenamiento", "\U0001F9E0"),
    ("prediccion", "Prediccion individual", "\U0001F4C8"),
    ("lotes", "Prediccion por lotes", "\U0001F4DA"),
    ("historial", "Historial", "\U0001F553"),
    ("evaluacion", "Evaluacion", "\U0001F4CA"),
    ("reportes", "Reportes", "\U0001F4C4"),
    ("configuracion", "Configuracion", "\U00002699"),
]


class VentanaPrincipal:
    """Ventana principal de la aplicacion ElectroPredict."""

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        self.root = root or tk.Tk()
        self.root.title("ElectroPredict - Predictor de Consumo Electrico")
        self.root.geometry("1280x780")
        self.root.minsize(1080, 660)

        # Estado compartido
        self.conexion = ConexionPostgreSQL()
        self.repositorio = RepositorioPostgreSQL(self.conexion)
        self.gestor = GestorDatos(self.repositorio)
        self.modelo = ModeloRegresionLineal()
        self.visualizador = VisualizadorGraficas()
        self.metricas: Optional[Dict[str, float]] = None
        self.info_entrenamiento: Optional[Dict[str, Any]] = None
        self.bd_conectada = False

        # Panel actual
        self._paneles: Dict[str, ttk.Frame] = {}
        self._botones_nav: Dict[str, tk.Button] = {}
        self._seccion_actual = "inicio"

        Tema(self.root).aplicar()

        self._construir_layout()
        self._crear_paneles()
        self.mostrar_seccion("inicio")

        # Conexion a base de datos en segundo plano
        self.root.after(200, self._conectar_bd_async)

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------
    def _construir_layout(self) -> None:
        # Contenedor raiz con dos columnas: sidebar + contenido
        self._contenedor = tk.Frame(self.root, bg=tema.COLOR_FONDO)
        self._contenedor.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = tk.Frame(self._contenedor, bg=tema.COLOR_SIDEBAR, width=230)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        self._construir_sidebar()

        # Area derecha
        self._area = tk.Frame(self._contenedor, bg=tema.COLOR_FONDO)
        self._area.pack(side="left", fill="both", expand=True)

        self._construir_encabezado()

        # Contenido desplazable
        self.frame_contenido = ttk.Frame(self._area, style="TFrame", padding=20)
        self.frame_contenido.pack(fill="both", expand=True)

        # Barra de estado
        self.barra_estado = BarraEstado(self._area)
        self.barra_estado.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

    def _construir_sidebar(self) -> None:
        logo = tk.Label(
            self._sidebar, text="\u26A1 ElectroPredict",
            bg=tema.COLOR_SIDEBAR, fg=tema.COLOR_TEXTO_CLARO,
            font=("Segoe UI", 15, "bold"), pady=22,
        )
        logo.pack(fill="x")

        subtitulo = tk.Label(
            self._sidebar, text="Predictor de consumo\nelectrico",
            bg=tema.COLOR_SIDEBAR, fg="#9aa7c7",
            font=("Segoe UI", 9), justify="center",
        )
        subtitulo.pack(fill="x", pady=(0, 16))

        for clave, etiqueta, icono in SECCIONES:
            boton = tk.Button(
                self._sidebar, text=f"  {icono}   {etiqueta}",
                anchor="w", relief="flat", bd=0,
                bg=tema.COLOR_SIDEBAR, fg=tema.COLOR_TEXTO_CLARO,
                activebackground=tema.COLOR_SIDEBAR_HOVER,
                activeforeground=tema.COLOR_TEXTO_CLARO,
                font=tema.FUENTE_MENU, padx=16, pady=11,
                cursor="hand2",
                command=lambda c=clave: self.mostrar_seccion(c),
            )
            boton.pack(fill="x")
            boton.bind("<Enter>", lambda e, b=boton, c=clave: self._hover_nav(b, c, True))
            boton.bind("<Leave>", lambda e, b=boton, c=clave: self._hover_nav(b, c, False))
            self._botones_nav[clave] = boton

        version = tk.Label(
            self._sidebar, text="Version 1.0.0",
            bg=tema.COLOR_SIDEBAR, fg="#6b7ba0", font=("Segoe UI", 8),
        )
        version.pack(side="bottom", fill="x", pady=10)

    def _hover_nav(self, boton: tk.Button, clave: str, entrando: bool) -> None:
        if clave == self._seccion_actual:
            return
        color = tema.COLOR_SIDEBAR_HOVER if entrando else tema.COLOR_SIDEBAR
        boton.configure(bg=color)

    def _construir_encabezado(self) -> None:
        encabezado = tk.Frame(self._area, bg=tema.COLOR_ENCABEZADO, height=64)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        self._lbl_seccion = tk.Label(
            encabezado, text="Inicio", bg=tema.COLOR_ENCABEZADO,
            fg=tema.COLOR_TEXTO, font=tema.FUENTE_TITULO,
        )
        self._lbl_seccion.pack(side="left", padx=20)

        self._lbl_saludo = tk.Label(
            encabezado, text="Bienvenido al sistema de prediccion",
            bg=tema.COLOR_ENCABEZADO, fg=tema.COLOR_TEXTO_SUAVE,
            font=tema.FUENTE_PEQUENA,
        )
        self._lbl_saludo.pack(side="right", padx=20)

    # ------------------------------------------------------------------
    # Gestion de paneles
    # ------------------------------------------------------------------
    def _crear_paneles(self) -> None:
        from interfaz.panel_inicio import PanelInicio
        from interfaz.panel_datos import PanelDatos
        from interfaz.panel_entrenamiento import PanelEntrenamiento
        from interfaz.panel_prediccion import PanelPrediccion
        from interfaz.panel_lotes import PanelLotes
        from interfaz.panel_historial import PanelHistorial
        from interfaz.panel_evaluacion import PanelEvaluacion
        from interfaz.panel_reportes import PanelReportes
        from interfaz.panel_configuracion import PanelConfiguracion

        clases = {
            "inicio": PanelInicio,
            "datos": PanelDatos,
            "entrenamiento": PanelEntrenamiento,
            "prediccion": PanelPrediccion,
            "lotes": PanelLotes,
            "historial": PanelHistorial,
            "evaluacion": PanelEvaluacion,
            "reportes": PanelReportes,
            "configuracion": PanelConfiguracion,
        }
        for clave, clase in clases.items():
            panel = clase(self.frame_contenido, self)
            panel.grid(row=0, column=0, sticky="nsew")
            self._paneles[clave] = panel

        self.frame_contenido.rowconfigure(0, weight=1)
        self.frame_contenido.columnconfigure(0, weight=1)

    def mostrar_seccion(self, clave: str) -> None:
        """Muestra una seccion y actualiza la navegacion."""
        if clave not in self._paneles:
            return

        panel = self._paneles[clave]
        panel.tkraise()
        self._seccion_actual = clave

        # Actualizar estilo de botones
        for c, boton in self._botones_nav.items():
            if c == clave:
                boton.configure(bg=tema.COLOR_SIDEBAR_ACTIVO,
                                font=tema.FUENTE_MENU_ACTIVO)
            else:
                boton.configure(bg=tema.COLOR_SIDEBAR, font=tema.FUENTE_MENU)

        for c, etiqueta, _ in SECCIONES:
            if c == clave:
                self._lbl_seccion.configure(text=etiqueta)
                break

        # Refrescar panel si expone el metodo
        if hasattr(panel, "refrescar"):
            try:
                panel.refrescar()
            except Exception as e:
                logger.error(f"Error refrescando panel {clave}: {e}")

    def actualizar_todo(self) -> None:
        """Refresca el panel actual y los indicadores globales."""
        self.barra_estado.set_estado_modelo(
            self.modelo.entrenado,
            self.metricas.get("r2") if self.metricas else None,
        )
        self.barra_estado.set_estado_bd(self.bd_conectada, self.conexion.configurada())
        panel = self._paneles.get(self._seccion_actual)
        if panel is not None and hasattr(panel, "refrescar"):
            try:
                panel.refrescar()
            except Exception as e:
                logger.error(f"Error actualizando panel: {e}")

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    def _conectar_bd_async(self) -> None:
        if not self.conexion.configurada():
            self.bd_conectada = False
            self.barra_estado.set_estado_bd(False, False)
            return

        def worker():
            conectado = self.conexion.conectar()
            if conectado:
                self.repositorio.inicializar_tablas()
                self.gestor.cargar_desde_bd()
            self.root.after(0, lambda: self._finalizar_conexion(conectado))

        threading.Thread(target=worker, daemon=True).start()

    def _finalizar_conexion(self, conectado: bool) -> None:
        self.bd_conectada = conectado
        self.barra_estado.set_estado_bd(conectado, self.conexion.configurada())
        if conectado:
            logger.info("Base de datos conectada y esquema inicializado")
        else:
            logger.warning("No se pudo conectar a la base de datos")
        self.actualizar_todo()

    def reconectar_bd(self, url: Optional[str] = None) -> bool:
        """Reconecta la base de datos (usado desde Configuracion)."""
        if url:
            os.environ["DATABASE_URL"] = url
            self.conexion = ConexionPostgreSQL(url)
            self.repositorio = RepositorioPostgreSQL(self.conexion)
            self.gestor.usar_repositorio(self.repositorio)
        conectado = self.conexion.conectar()
        if conectado:
            self.repositorio.inicializar_tablas()
            self.gestor.cargar_desde_bd()
        self.bd_conectada = conectado
        self.actualizar_todo()
        return conectado

    # ------------------------------------------------------------------
    # Utilidades compartidas
    # ------------------------------------------------------------------
    def mostrar_mensaje(self, titulo: str, mensaje: str, tipo: str = "info") -> None:
        mostrar_mensaje(self.root, titulo, mensaje, tipo)

    def esta_entrenado(self) -> bool:
        return self.modelo.entrenado

    def registrar_entrenamiento(self, info: Dict[str, Any]) -> None:
        self.info_entrenamiento = info
        self.metricas = info.get("metricas")
        self.gestor.registrar_entrenamiento(info)

    def crear_modelo(self, algoritmo: str = "lineal", imputar: bool = False) -> None:
        """Reemplaza el modelo actual por uno nuevo segun el algoritmo elegido."""
        self.modelo = ModeloRegresionLineal(algoritmo=algoritmo, imputar=imputar)
        self.metricas = None
        self.info_entrenamiento = None

    def cargar_modelo_en_app(self, modelo: ModeloRegresionLineal) -> None:
        """Sustituye el modelo de la aplicacion por uno cargado desde disco."""
        self.modelo = modelo
        self.metricas = modelo.metricas
        coeficientes = (
            dict(zip(modelo.feature_names, modelo.coeficientes))
            if modelo.coeficientes is not None else {}
        )
        self.info_entrenamiento = {
            "algoritmo": modelo.algoritmo,
            "algoritmo_nombre": modelo.algoritmo_nombre,
            "imputacion": modelo.imputar,
            "num_registros": modelo.n_entrenamiento + modelo.n_prueba,
            "registros_entrenamiento": modelo.n_entrenamiento,
            "registros_prueba": modelo.n_prueba,
            "coeficientes": coeficientes,
            "intercepto": modelo.intercepto,
            "version": modelo.version,
        }

    def run(self) -> None:
        self.root.mainloop()

    def mainloop(self) -> None:
        self.root.mainloop()
