from fastapi import APIRouter

# Módulos modularizados (carpetas)
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.clients import router as clients_router
from app.api.v1.endpoints.dev_tools import router as dev_tools_router

# Módulos simples (archivos)
from app.api.v1.endpoints import users, inventory, sales, appointments, config, purchases, services, dashboard, user_management, statistics, suppliers, health, support

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/login", tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(user_management.router, prefix="/user-management", tags=["user-management"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(suppliers.router)  # Ya tiene prefix="/suppliers" interno
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(dev_tools_router, prefix="/dev-tools", tags=["dev-tools"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(support.router, prefix="/support", tags=["support"])


