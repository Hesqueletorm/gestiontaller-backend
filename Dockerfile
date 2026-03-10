# ==========================================
# Dockerfile para Backend - Gestión de Taller
# Python FastAPI + Gunicorn (Producción)
# ==========================================

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Dependencias del sistema para psycopg2 y healthcheck
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python (cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar código
COPY . .

# Crear directorio de uploads y logs + permisos entrypoint
RUN mkdir -p /app/uploads/avatars /app/logs && \
    chmod +x /app/entrypoint.sh

# Usuario no-root
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint: espera BD + migraciones, luego arranca Gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
