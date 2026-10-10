"""Punto de entrada principal de ElectroPredict.

Aplicacion de escritorio para predecir consumo electrico usando
regresion lineal multiple con interfaz Tkinter moderna.
"""
import sys
import logging

# Cargar variables de entorno desde .env si python-dotenv esta disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv es opcional
    pass

import tkinter as tk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ElectroPredict")


def main() -> None:
    """Punto de entrada de la aplicacion."""
    try:
        logger.info("Iniciando ElectroPredict...")
        root = tk.Tk()
        from interfaz.ventana_principal import VentanaPrincipal
        app = VentanaPrincipal(root)
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Aplicacion interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
