"""
Router agregador para endpoints de poblar datos de prueba

Módulos especializados:
- populate_clients: Clientes, vehículos y visitas
- populate_appointments: Turnos y citas
- populate_inventory: Productos, categorías y servicios  
- populate_sales: Ventas y comprobantes
- populate_purchases: Compras y proveedores
"""
from fastapi import APIRouter

from .populate_clients import router as clients_router
from .populate_appointments import router as appointments_router
from .populate_inventory import router as inventory_router
from .populate_sales import router as sales_router
from .populate_purchases import router as purchases_router

router = APIRouter()

# Incluir todos los sub-routers de populate
router.include_router(clients_router)
router.include_router(appointments_router)
router.include_router(inventory_router)
router.include_router(sales_router)
router.include_router(purchases_router)
