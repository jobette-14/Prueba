# Dockerfile de ElectroPredict (API + frontend web).
# Construye el frontend React/Vite y luego empaqueta la API FastAPI que lo sirve.
#
# Uso:
#   docker build -t electropredict .
#   docker run -p 8000:8000 --env-file web/.env electropredict

# ---------- Etapa 1: compilar el frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /app/web/frontend
COPY web/frontend/package*.json ./
RUN npm install
COPY web/frontend/ ./
RUN npm run build

# ---------- Etapa 2: API + nucleo compartido ----------
FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
COPY web/requirements.txt ./web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

COPY . .
COPY --from=frontend /app/web/frontend/dist ./web/frontend/dist

EXPOSE 8000
CMD ["uvicorn", "web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
