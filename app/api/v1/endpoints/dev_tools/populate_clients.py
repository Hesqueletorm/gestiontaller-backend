"""
Endpoints para poblar clientes, vehículos y visitas
"""
from typing import Any
import random
from datetime import timedelta, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.client import Client, Vehicle, Visit

from .schemas import DevToolResponse
from .catalogs import (
    generar_nombre_completo, generar_email,
    generar_telefono, generar_direccion, generar_vehiculo
)

router = APIRouter()


@router.post("/populate/clients", response_model=DevToolResponse)
def populate_clients(
    n: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar clientes de prueba con vehículos."""
    try:
        count = 0
        for _ in range(n):
            nombre = generar_nombre_completo()
            email = generar_email(nombre)
            telefono = generar_telefono()
            direccion = generar_direccion()
            
            cliente = Client(
                lubricentro_id=current_user.lubricentro_id,
                nombre=nombre,
                email=email,
                telefono=telefono,
                direccion=direccion,
                notas="Cliente generado por bot de desarrollo"
            )
            db.add(cliente)
            db.flush()
            
            # Agregar entre 1 y 3 vehículos
            if random.random() <= 0.9:
                for _ in range(random.randint(1, 3)):
                    vehiculo_data = generar_vehiculo()
                    vehiculo = Vehicle(
                        cliente_id=cliente.id,
                        marca=vehiculo_data["marca"],
                        version=vehiculo_data["version"],
                        modelo=vehiculo_data["modelo"],
                        patente=vehiculo_data["patente"],
                        kilometraje=vehiculo_data["kilometraje"],
                        descripcion=vehiculo_data["descripcion"]
                    )
                    db.add(vehiculo)
            
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} clientes generados con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar clientes: {str(e)}")


@router.post("/populate/visits", response_model=DevToolResponse)
def populate_visits(
    n: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar visitas/historial de clientes."""
    try:
        clientes = db.query(Client).filter(
            Client.lubricentro_id == current_user.lubricentro_id
        ).all()
        
        if not clientes:
            return DevToolResponse(
                success=False, 
                message="⚠️ No hay clientes. Genere clientes primero.",
                count=0
            )
        
        hoy = date.today()
        observaciones = [
            "Servicio completo realizado",
            "Cliente satisfecho con el trabajo",
            "Se recomendó próximo cambio en 10.000 km",
            "Vehículo en buen estado general",
            "Se detectó desgaste en pastillas",
            "Próximo servicio programado",
            ""
        ]
        
        count = 0
        for _ in range(n):
            cliente = random.choice(clientes)
            
            vehiculos = db.query(Vehicle).filter(Vehicle.cliente_id == cliente.id).all()
            if vehiculos:
                vehiculo = random.choice(vehiculos)
                vehiculo_desc = vehiculo.descripcion or f"{vehiculo.marca} {vehiculo.version} {vehiculo.modelo}"
                km = vehiculo.kilometraje or random.randint(10000, 250000)
            else:
                vehiculo_data = generar_vehiculo()
                vehiculo_desc = vehiculo_data["descripcion"]
                km = vehiculo_data["kilometraje"]
            
            fecha = (hoy - timedelta(days=random.randint(0, 365))).isoformat()
            
            visita = Visit(
                cliente_id=cliente.id,
                lubricentro_id=current_user.lubricentro_id,
                fecha=fecha,
                vehiculo_descripcion=vehiculo_desc,
                kilometraje=km,
                observacion=random.choice(observaciones)
            )
            db.add(visita)
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} visitas generadas con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar visitas: {str(e)}")
