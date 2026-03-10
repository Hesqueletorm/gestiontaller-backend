# Script para crear la tabla de servicios
import sys
sys.path.insert(0, '.')

from app.db.session import engine, SessionLocal
from app.db.base import Base  # Importar todos los modelos

# Crear tabla
from app.models.inventory import Servicio
Servicio.__table__.create(bind=engine, checkfirst=True)

print("✓ Tabla 'servicios' creada correctamente")

# Insertar algunos servicios de ejemplo
db = SessionLocal()

# Verificar si ya hay servicios
count = db.query(Servicio).count()
if count == 0:
    servicios_ejemplo = [
        {"nombre": "Cambio de aceite", "precio": 5000, "categoria": "Mantenimiento"},
        {"nombre": "Cambio de filtro de aceite", "precio": 1500, "categoria": "Mantenimiento"},
        {"nombre": "Cambio de filtro de aire", "precio": 1200, "categoria": "Mantenimiento"},
        {"nombre": "Cambio de filtro de combustible", "precio": 1800, "categoria": "Mantenimiento"},
        {"nombre": "Alineación y balanceo", "precio": 8000, "categoria": "Neumáticos"},
        {"nombre": "Rotación de neumáticos", "precio": 2500, "categoria": "Neumáticos"},
        {"nombre": "Revisión de frenos", "precio": 3000, "categoria": "Frenos"},
        {"nombre": "Cambio de pastillas de freno", "precio": 6000, "categoria": "Frenos"},
        {"nombre": "Diagnóstico computarizado", "precio": 4000, "categoria": "Diagnóstico"},
        {"nombre": "Escaneo de códigos de error", "precio": 2000, "categoria": "Diagnóstico"},
        {"nombre": "Lavado de motor", "precio": 3500, "categoria": "Limpieza"},
        {"nombre": "Limpieza de inyectores", "precio": 5500, "categoria": "Motor"},
        {"nombre": "Cambio de bujías", "precio": 4500, "categoria": "Motor"},
        {"nombre": "Revisión general", "precio": 2500, "categoria": "General"},
        {"nombre": "Mano de obra general", "precio": 0, "categoria": "General"},
    ]
    
    for serv in servicios_ejemplo:
        nuevo = Servicio(
            lubricentro_id=1,
            nombre=serv["nombre"],
            precio=serv["precio"],
            categoria=serv["categoria"],
            activo=1
        )
        db.add(nuevo)
    
    db.commit()
    print(f"✓ {len(servicios_ejemplo)} servicios de ejemplo insertados")
else:
    print(f"→ Ya existen {count} servicios en la base de datos")

db.close()
