# Guia de instalacion y uso

## A) Aplicacion de escritorio (Windows)

### Instalacion
1. Descarga `ElectroPredict-Setup-1.1.0.exe`.
2. Ejecutalo y sigue el asistente (puedes elegir acceso directo en el escritorio).
3. Abre **ElectroPredict** desde el menu Inicio o el escritorio.

No necesitas instalar Python: el ejecutable incluye todo lo necesario.

### Uso rapido
1. **Datos**: importa un CSV de ejemplo (`ejemplos/`) o registra datos manualmente.
2. **Entrenamiento**: elige algoritmo (Lineal / Ridge / Random Forest), marca
   *imputar* si hay valores faltantes y pulsa **Entrenar**. Puedes **Comparar**
   algoritmos y **Guardar/Cargar** el modelo (`.pkl`).
3. **Evaluacion / Prediccion**: introduce temperatura, personas, horas de uso y
   consumo anterior para estimar el consumo.
4. **Reportes**: genera TXT, CSV o PDF.
5. **Base de datos / Ajustes**: conecta PostgreSQL pegando `DATABASE_URL`.

### Desinstalacion
Panel de control → *Programas* → **ElectroPredict** → Desinstalar.
(Tus modelos guardados en documentos no se eliminan.)

---

## B) Version web

### Con Docker (local)
```bash
docker build -t electropredict .
docker run -p 8000:8000 --env-file web/.env electropredict
```
Abre `http://localhost:8000`.

### Sin Docker (desarrollo)
```bash
# Backend
pip install -r requirements.txt -r web/requirements.txt
python -m uvicorn web.api.main:app --reload --port 8000

# Frontend (otra terminal)
cd web/frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api -> 8000)
```

### Produccion
Compila el frontend (`npm run build` en `web/frontend`) y sirve todo con la API
(FastAPI monta `web/frontend/dist`). Ver `DESPLIEGUE.md`.

---

## Solucion de problemas

| Sintoma | Causa probable | Solucion |
|---------|----------------|----------|
| La web no muestra la SPA | Frontend sin compilar | `npm run build` en `web/frontend` |
| `base_datos_conectada: false` | Sin `DATABASE_URL` o sin red | Revisa la cadena y `sslmode=require` |
| 401/403 al entrenar/registrar | Falta `X-API-Key` | Define `ELECTROPREDICT_API_KEY` y enviala |
| 429 | Limite superado | Ajusta `RATE_LIMIT` o espera |
| El chat responde "no disponible" | Sin `CHAT_API_KEY` | Es opcional; configura la clave para activarlo |
| El `.exe` no arranca | Antivirus/SmartScreen | Permitir la app; es un binario firmado localmente |
