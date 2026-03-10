"""
Módulo de Clientes - Router principal
Combina los sub-routers de CRUD, vehículos y validaciones
"""
from fastapi import APIRouter
from .crud import router as crud_router
from .vehicles import router as vehicles_router
from .validation import router as validation_router
from .schemas import ClientListResponse, VehicleKmUpdate, ValidateClientData, ValidateResponse

router = APIRouter()

# Incluir todos los sub-routers
router.include_router(crud_router)
router.include_router(vehicles_router)
router.include_router(validation_router)
