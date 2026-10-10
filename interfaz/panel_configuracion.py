"""Panel de Configuracion de ElectroPredict.

Permite configurar la conexion a PostgreSQL/Neon, probar la conexion e
inicializar el esquema. Tambien documenta los rangos de validacion.
"""

import logging
import tkinter as tk
from tkinter import ttk

from interfaz import tema
from base_datos.conexion import limpiar_url

logger = logging.getLogger(__name__)


class PanelConfiguracion(ttk.Frame):
    """Configuracion de base de datos y parametros del sistema."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        ttk.Label(self, text="Conexion a PostgreSQL / Neon",
                  style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 6))

        ttk.Label(
            self, style="TLabel", wraplength=860, justify="left",
            text=("La URL de conexion se obtiene de la variable de entorno DATABASE_URL. "
                  "Puede definirla en un archivo .env (copie .env.example) o introducirla "
                  "temporalmente aqui para esta sesion. No se almacenan credenciales en el codigo."),
        ).pack(anchor="w", pady=(0, 12))

        fila = ttk.Frame(self, style="TFrame")
        fila.pack(fill="x", pady=(0, 8))
        ttk.Label(fila, text="DATABASE_URL:", style="TLabel").pack(side="left")
        self._entry_url = ttk.Entry(fila, width=70, show="*")
        self._entry_url.pack(side="left", padx=8)
        ttk.Button(fila, text="Aplicar y conectar",
                   command=self._aplicar).pack(side="left")

        botones = ttk.Frame(self, style="TFrame")
        botones.pack(fill="x", pady=(4, 12))
        ttk.Button(botones, text="Probar conexion",
                   command=self._probar).pack(side="left")
        ttk.Button(botones, text="Inicializar tablas",
                   command=self._inicializar).pack(side="left", padx=8)

        self._lbl_estado = ttk.Label(self, text="", style="TLabel", wraplength=860)
        self._lbl_estado.pack(anchor="w", pady=(0, 14))

        # Documentacion de rangos
        ttk.Label(self, text="Rangos de validacion", style="Subtitulo.TLabel").pack(
            anchor="w", pady=(10, 6))
        rangos = (
            "Temperatura: -50 C a 60 C  (rango ambiental razonable para consumo domestico)\n"
            "Personas:    1 a 50         (ocupantes de una vivienda)\n"
            "Horas de uso: 0 a 24        (no puede exceder las horas de un dia)\n"
            "Consumo anterior: 0 a 1000 kWh\n"
            "Consumo real:     0 a 1000 kWh\n\n"
            "Estos limites son configuracion de la aplicacion; editar en datos/validaciones.py."
        )
        ttk.Label(self, text=rangos, style="TLabel", justify="left").pack(anchor="w")

    def refrescar(self) -> None:
        url = self.app.conexion.obtener_url_segura() if hasattr(
            self.app.conexion, "obtener_url_segura") else "***"
        configurada = self.app.conexion.configurada()
        if self.app.bd_conectada:
            self._lbl_estado.configure(
                text=f"Estado: CONECTADA\nURL: {url}", foreground=tema.COLOR_EXITO)
        elif configurada:
            self._lbl_estado.configure(
                text=f"Estado: NO CONECTADA (hay URL configurada)\nURL: {url}",
                foreground=tema.COLOR_ERROR)
        else:
            self._lbl_estado.configure(
                text=("Estado: NO CONFIGURADA. La aplicacion funciona en modo memoria "
                      "durante esta sesion. Configure DATABASE_URL para persistir."),
                foreground=tema.COLOR_ADVERTENCIA)

    def _aplicar(self) -> None:
        url = self._entry_url.get().strip()
        if not url:
            self.app.mostrar_mensaje("URL vacia", "Introduzca una DATABASE_URL valida.", "warning")
            return
        exito = self.app.reconectar_bd(url)
        self.refrescar()
        if exito:
            self.app.mostrar_mensaje("Conexion establecida",
                                     "La base de datos se conecto correctamente.", "success")
        else:
            self.app.mostrar_mensaje("Error de conexion",
                                     "No se pudo conectar con la URL proporcionada.", "error")

    def _probar(self) -> None:
        if not self.app.conexion.esta_conectado:
            self.app.mostrar_mensaje("Sin conexion",
                                     "No hay una conexion activa. Aplique una DATABASE_URL.", "warning")
            return
        saludable = self.app.conexion.verificar_conexion_salud()
        if saludable:
            self.app.mostrar_mensaje("Conexion saludable",
                                     "La base de datos responde correctamente.", "success")
        else:
            self.app.mostrar_mensaje("Conexion con problemas",
                                     "No se obtuvo respuesta de la base de datos.", "error")

    def _inicializar(self) -> None:
        if not self.app.conexion.esta_conectado:
            self.app.mostrar_mensaje("Sin conexion",
                                     "Conecte primero a la base de datos.", "warning")
            return
        if self.app.repositorio.inicializar_tablas():
            self.app.mostrar_mensaje("Esquema listo",
                                     "Las tablas fueron creadas o ya existian.", "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo inicializar el esquema.", "error")
