"""
Endpoints para poblar turnos/citas
"""
from typing import Any
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.client import Client
from app.models.appointments import Appointment

from .schemas import DevToolResponse

router = APIRouter()


@router.post("/populate/appointments", response_model=DevToolResponse)
def populate_appointments(
    n: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Generar turnos de prueba."""
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
        
        servicios = ["Cambio de Aceite", "Filtros", "Alineación", "Balanceo", "Revisión General", "Frenos"]
        vehiculos_modelos = ["Ford Fiesta", "Fiat Cronos", "Toyota Hilux", "VW Gol", "Peugeot 208", "Chevrolet Onix"]
        
        count = 0
        intentos = 0
        max_intentos = n * 5
        
        while count < n and intentos < max_intentos:
            intentos += 1
            cliente = random.choice(clientes)
            fecha = (datetime.now() + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            hora_int = random.randint(9, 18)
            minutos = random.choice(['00', '30'])
            hora = f"{hora_int:02d}:{minutos}"
            
            existe = db.query(Appointment).filter(
                Appointment.lubricentro_id == current_user.lubricentro_id,
                Appointment.fecha == fecha,
                Appointment.hora == hora
            ).first()
            
            if existe:
                continue
            
            turno = Appointment(
                lubricentro_id=current_user.lubricentro_id,
                fecha=fecha,
                hora=hora,
                cliente=cliente.nombre,
                vehiculo=random.choice(vehiculos_modelos),
                servicio=random.choice(servicios),
                notas="Turno generado por bot de desarrollo",
                duracion=30
            )
            db.add(turno)
            db.flush()
            count += 1
        
        db.commit()
        return DevToolResponse(success=True, message=f"✅ {count} turnos generados con éxito", count=count)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al generar turnos: {str(e)}")
