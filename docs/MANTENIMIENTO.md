# Guia de mantenimiento

## Estructura

```
ElectroPredict/
  interfaz/          UI de escritorio (Tkinter)
  modelo/            Nucleo ML compartido (entrenamiento, persistencia)
  datos/             Carga, validacion, gestor (CSV/BD)   <- compartido
  base_datos/        Conexion y repositorio PostgreSQL     <- compartido
  graficas/          Graficos (matplotlib) para escritorio
  reportes/          Reportes TXT/CSV/PDF                  <- compartido
  web/
    api/             API FastAPI (config, estado, routers) <- compartido
    frontend/        SPA React/Vite
  empaquetado/       PyInstaller (.spec) + Inno Setup (.iss)
  tests/             Pruebas del nucleo y de la API
  docs/              Documentacion
  ejemplos/          CSV de ejemplo
```

> **Regla clave:** la logica de prediccion vive en `modelo/`, `datos/` y
> `base_datos/`. Tanto el escritorio como la web la **reutilizan**; nunca se
> duplica.

## Ejecutar pruebas

```bash
python -m pytest tests -q
```

Incluye consistencia web↔escritorio (`tests/test_consistencia_web.py`):
misma prediccion y mismas metricas en ambos modos.

## Tareas frecuentes

| Tarea | Comando |
|-------|---------|
| Recompilar frontend | `cd web/frontend; npm run build` |
| Recompilar exe | `powershell -File empaquetado\build_exe.ps1` |
| Recompilar instalador | `ISCC.exe empaquetado\instalador.iss` |
| Build Docker | `docker build -t electropredict .` |
| Pruebas | `python -m pytest tests -q` |

## Actualizar dependencias

```bash
pip install --upgrade -r requirements.txt -r web/requirements.txt
cd web/frontend; npm update
```
Revisa que `python -m pytest tests -q` siga en verde antes de publicar.

## Versionado y releases

1. Sube la version en `empaquetado/instalador.iss` y `empaquetado/version_info.txt`.
2. `git tag v1.1.0 && git push --tags` → el workflow **Build Windows** compila el
   instalador.
3. Adjunta el `.exe` a la release de GitHub.

## Buenas practicas de seguridad

- Secretos solo por variables de entorno; `.env` en `.gitignore`.
- Consultas SQL parametrizadas (`%s`); nunca concatenar SQL.
- CORS restringido en produccion (nunca `*`).
- Limite de peticiones (`RATE_LIMIT`) y `X-API-Key` en rutas de escritura.
- Los errores 500 no revelan detalles internos al cliente.

## Registro de errores (plantilla)

| Fecha | Modulo | Descripcion | Estado | Solucion |
|-------|--------|-------------|--------|----------|
| 2026-10-10 | web/api/estado.py | Los tests guardaban modelos en `modelos/` del proyecto | Resuelto | `guardar_modelo` acepta `directorio`; tests usan tmp |
