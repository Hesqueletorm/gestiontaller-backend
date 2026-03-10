"""
Módulo de Autenticación - Router principal
Combina los sub-routers de login, registro, recuperación y 2FA
"""
from fastapi import APIRouter
from .login import router as login_router
from .register import router as register_router  
from .recovery import router as recovery_router
from .two_factor import router as two_factor_router
from .utils import codigos_pendientes, codigos_recuperacion

router = APIRouter()

# Incluir todos los sub-routers
router.include_router(login_router, tags=["auth"])
router.include_router(register_router, tags=["auth"])
router.include_router(recovery_router, tags=["auth"])
router.include_router(two_factor_router, prefix="/2fa", tags=["2fa"])
