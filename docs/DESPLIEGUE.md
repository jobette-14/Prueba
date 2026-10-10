# Guia de despliegue

ElectroPredict tiene **dos modalidades**:

1. **Aplicacion de escritorio** (Windows): se distribuye como instalador `.exe`.
2. **Version web**: API FastAPI + frontend React compilado, desplegable en la nube.

La base de datos es **PostgreSQL** (recomendado: [Neon](https://neon.tech)).
Sin `DATABASE_URL` la app funciona en **modo memoria** (no persiste entre reinicios).

---

## 1. Desplegar la version web

### 1.1 Requisitos

- Repositorio en GitHub (rama `main`/`master`).
- Una base de datos PostgreSQL/Neon y su cadena `DATABASE_URL`.
- Una clave de API para proteger escritura (`ELECTROPREDICT_API_KEY`).

### 1.2 Opcion A: Render (Docker, recomendado)

1. En Render: **New + → Blueprint** y conecta el repositorio.
2. Render leera `render.yaml` y creara el servicio Docker.
3. Define los secretos (`sync: false`):
   - `DATABASE_URL` → cadena de Neon (`postgresql://...?sslmode=require`)
   - `CORS_ORIGINS` → tu dominio de Render (p. ej. `https://electropredict.onrender.com`)
   - `CHAT_API_KEY` → opcional
4. Espera el build. Comprueba `https://TU-SERVICIO/api/salud`.

### 1.3 Opcion B: Fly.io

```bash
fly launch --no-deploy
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set ELECTROPREDICT_API_KEY="una-clave-larga"
fly secrets set CORS_ORIGINS="https://tu-dominio"
fly deploy
```

### 1.4 Opcion C: Cualquier host con Docker

```bash
docker build -t electropredict .
docker run -p 8000:8000 --env-file web/.env electropredict
```

La imagen compila el frontend (Node) y sirve la API + SPA en el puerto 8000.

### 1.5 Variables de entorno

Ver `web/.env.example`. Claves principales:

| Variable | Descripcion |
|----------|-------------|
| `ENTORNO` | `desarrollo` o `produccion` |
| `DATABASE_URL` | Cadena de Neon/PostgreSQL (**secreto**) |
| `ELECTROPREDICT_API_KEY` | Clave para rutas de escritura (**secreto**) |
| `CORS_ORIGINS` | Origenes permitidos (coma), en produccion nunca `*` |
| `RATE_LIMIT` | Limite por IP (p. ej. `120/minute`) |
| `CHAT_ENABLED` / `CHAT_API_KEY` / `CHAT_BASE_URL` / `CHAT_MODEL` | Chat IA opcional |

> **Nunca** subas `.env` al repositorio ni incluyas secretos en el frontend.

### 1.6 Base de datos (Neon)

1. Crea el proyecto y copia la cadena de conexion con `sslmode=require`.
2. Pegala en `DATABASE_URL` del hosting.
3. Al iniciar, la API crea las tablas necesarias si no existen.
4. Comprueba en `/api/salud` que `base_datos_conectada` sea `true`.

---

## 2. Distribuir la aplicacion de escritorio

### 2.1 Compilar localmente (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File empaquetado\build_exe.ps1
# Genera: dist\ElectroPredict.exe
```

Instalador (requiere [Inno Setup 6](https://jrsoftware.org/isinfo.php)):

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" empaquetado\instalador.iss
# Genera: empaquetado\dist\ElectroPredict-Setup-1.1.0.exe
```

### 2.2 Compilar en la nube (sin PC Windows)

Ejecuta el workflow **Build Windows** (`.github/workflows/build-windows.yml`):
`Actions → Build Windows → Run workflow`, o crea un tag `v1.1.0`. El instalador
queda como artefacto descargable.

### 2.3 Publicar la descarga

Adjunta `ElectroPredict-Setup-1.1.0.exe` a una **Release** de GitHub. Enlaza esa
release desde la web (pagina de descarga).

---

## 3. Actualizaciones

- **Web**: sube los cambios a la rama principal; el hosting redespliega solo.
- **Escritorio**: aumenta `AppVersion` en `empaquetado/instalador.iss` y
  `version_info.txt`, recompila y publica una nueva release. El instalador
  actualiza por encima de la version anterior.
