from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.init_db import init_db, create_default_user

# Importar middleware de seguridad
from app.core.security.middleware import SecurityMiddleware, RateLimitMiddleware

# Crear directorio de uploads si no existe
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(os.path.join(UPLOADS_DIR, "avatars"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de startup y shutdown"""
    # Startup: Inicializar DB y crear usuario admin
    print("[main] Inicializando base de datos...")
    init_db()
    
    db = SessionLocal()
    try:
        create_default_user(db)
    finally:
        db.close()
    
    print("[main] Backend listo!")
    yield
    # Shutdown
    print("[main] Cerrando backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# ============== CORS ==============
# CORS DEBE estar PRIMERO (agregado último) para responder a preflight OPTIONS
# En desarrollo local siempre permitir localhost
# En producción configurar BACKEND_CORS_ORIGINS en .env

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
] + settings.BACKEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
    max_age=600,
)

# ============== MIDDLEWARE DE SEGURIDAD ==============
# El orden importa: se ejecutan de abajo hacia arriba en la request
# y de arriba hacia abajo en la response

# 1. Security Headers (primero para aplicar headers a todas las respuestas)
app.add_middleware(SecurityMiddleware)

# 2. Rate Limiting por IP (DESPUÉS de CORS para no bloquear preflight)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,  # Límite global por IP
    exempt_paths=["/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"]
)


app.include_router(api_router, prefix=settings.API_V1_STR)

# Montar directorio de archivos estáticos (fotos de perfil, etc.)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.get("/")
def root():
    return {"message": "Welcome to LubricentroM API"}

