"""
Módulo de Herramientas de Desarrollador - Router principal
"""
from fastapi import APIRouter
from .populate import router as populate_router
from .cache import router as cache_router
from .stats import router as stats_router
from .schemas import DevToolResponse, CacheLimpiezaResponse

router = APIRouter()

# Incluir todos los sub-routers
router.include_router(populate_router)
router.include_router(cache_router)
router.include_router(stats_router)
