#!/bin/bash
# ==========================================
# Entrypoint para Backend en producción
# Espera BD, crea tablas y arranca el server
# ==========================================
set -e

echo "=== Gestión de Taller - Backend ==="
echo "[1/3] Esperando que PostgreSQL esté listo..."

# Esperar a que la BD esté disponible (max 30 intentos)
for i in $(seq 1 30); do
    python -c "
from app.core.config import settings
from sqlalchemy import create_engine
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
conn.close()
print('PostgreSQL conectado!')
" && break
    echo "  Intento $i/30 - BD no disponible, esperando 2s..."
    sleep 2
done

echo "[2/3] Inicializando tablas de base de datos..."
python -c "
from app.db.init_db import init_db
init_db()
print('Tablas creadas/verificadas.')
"

echo "[3/3] Iniciando servidor..."
exec "$@"
