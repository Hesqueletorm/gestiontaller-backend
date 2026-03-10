from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_appointment import appointment as crud_appointment
from app.schemas.appointment_schema import Appointment, AppointmentCreate, AppointmentUpdate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Appointment])
def read_appointments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener todos los turnos del lubricentro del usuario"""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    return crud_appointment.get_by_lubricentro(
        db, lubricentro_id=current_user.lubricentro_id, skip=skip, limit=limit
    )


@router.get("/fecha/{fecha}", response_model=List[Appointment])
def read_appointments_by_fecha(
    fecha: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener turnos de un día específico (formato YYYY-MM-DD)"""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    return crud_appointment.get_by_fecha(
        db, lubricentro_id=current_user.lubricentro_id, fecha=fecha
    )


@router.get("/rango", response_model=List[Appointment])
def read_appointments_by_rango(
    desde: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    hasta: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener turnos en un rango de fechas"""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    return crud_appointment.get_by_rango(
        db, lubricentro_id=current_user.lubricentro_id, fecha_desde=desde, fecha_hasta=hasta
    )


@router.get("/proximos")
def read_proximos_turnos(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Obtener turnos para notificaciones:
    - Turnos pasados de hoy (que se pasaron)
    - Turnos de las próximas 3 horas
    """
    from datetime import datetime, timedelta
    
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    now = datetime.now()
    fecha_hoy = now.strftime("%Y-%m-%d")
    hora_actual = now.strftime("%H:%M")
    hora_limite = (now + timedelta(hours=3)).strftime("%H:%M")
    
    # Obtener todos los turnos de hoy
    turnos_hoy = crud_appointment.get_by_fecha(
        db, lubricentro_id=current_user.lubricentro_id, fecha=fecha_hoy
    )
    
    resultado = []
    for turno in turnos_hoy:
        # Determinar estado del turno
        if turno.hora < hora_actual:
            estado = "pasado"  # Turno que ya pasó
        elif turno.hora <= hora_limite:
            estado = "proximo"  # Turno en próximas 3 horas
        else:
            continue  # Turno muy lejano, no incluir
        
        # Agregar nombre del cliente si existe cliente_id
        cliente_nombre = None
        cliente_id = getattr(turno, 'cliente_id', None)  # Acceso seguro
        if cliente_id:
            from app.models.client import Client as ClientModel
            cliente = db.query(ClientModel).filter(ClientModel.id == cliente_id).first()
            if cliente:
                cliente_nombre = cliente.nombre
        
        # Construir respuesta con estado
        turno_dict = {
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "cliente": turno.cliente,
            "vehiculo": turno.vehiculo,
            "servicio": turno.servicio,
            "notas": turno.notas,
            "duracion": turno.duracion,
            "lubricentro_id": turno.lubricentro_id,
            "cliente_id": cliente_id,
            "cliente_nombre": cliente_nombre,
            "estado": estado  # "pasado" o "proximo"
        }
        resultado.append(turno_dict)
    
    # Ordenar: primero los pasados (más recientes), luego los próximos
    resultado.sort(key=lambda x: (x["estado"] != "pasado", x["hora"]))
    
    return resultado


@router.post("/", response_model=Appointment)
def create_appointment(
    *,
    db: Session = Depends(deps.get_db),
    appointment_in: AppointmentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Crear un nuevo turno"""
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    # Verificar si el slot está disponible
    if not crud_appointment.check_slot_disponible(
        db, lubricentro_id=current_user.lubricentro_id, 
        fecha=appointment_in.fecha, hora=appointment_in.hora
    ):
        raise HTTPException(status_code=400, detail="El horario ya está ocupado")
    
    return crud_appointment.create_with_lubricentro(
        db, obj_in=appointment_in, lubricentro_id=current_user.lubricentro_id
    )


@router.get("/{turno_id}", response_model=Appointment)
def read_appointment(
    turno_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Obtener un turno por ID"""
    turno = crud_appointment.get(db, id=turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if turno.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    return turno


@router.put("/{turno_id}", response_model=Appointment)
def update_appointment(
    turno_id: int,
    *,
    db: Session = Depends(deps.get_db),
    appointment_in: AppointmentUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Actualizar un turno existente"""
    turno = crud_appointment.get(db, id=turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if turno.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Si cambió fecha/hora, verificar disponibilidad
    new_fecha = appointment_in.fecha or turno.fecha
    new_hora = appointment_in.hora or turno.hora
    if new_fecha != turno.fecha or new_hora != turno.hora:
        if not crud_appointment.check_slot_disponible(
            db, lubricentro_id=current_user.lubricentro_id,
            fecha=new_fecha, hora=new_hora, exclude_id=turno_id
        ):
            raise HTTPException(status_code=400, detail="El nuevo horario ya está ocupado")
    
    return crud_appointment.update_turno(db, db_obj=turno, obj_in=appointment_in)


@router.delete("/{turno_id}")
def delete_appointment(
    turno_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Eliminar un turno"""
    turno = crud_appointment.get(db, id=turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if turno.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    crud_appointment.remove(db, id=turno_id)
    return {"ok": True, "message": "Turno eliminado"}
