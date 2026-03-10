"""
Router agregador de endpoints CRUD de Clientes

Módulos especializados:
- read: Endpoints GET (listar, buscar, detalle, visitas)
- write: Endpoints POST/PUT/DELETE (crear, sync, actualizar, eliminar)
"""
from fastapi import APIRouter

from .read import router as read_router
from .write import router as write_router

router = APIRouter()

# Incluir todos los sub-routers
router.include_router(read_router)
router.include_router(write_router)
