"""
Endpoints de Validación de Clientes
"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.models.client import Client as ClientModel, Vehicle as VehicleModel
from app.models.user import User
from .schemas import ValidateClientData, ValidateResponse, ConflictDetail

router = APIRouter()


@router.post("/validate-unique", response_model=ValidateResponse)
def validate_client_unique(
    *,
    db: Session = Depends(deps.get_db),
    data: ValidateClientData,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Validar que email y patentes no pertenezcan a otro cliente.
    Si pertenecen a otro cliente, devuelve conflicto.
    """
    conflicts = []
    
    # Validar email
    if data.email and data.email.strip():
        email_lower = data.email.strip().lower()
        client_with_email = db.query(ClientModel).filter(
            ClientModel.lubricentro_id == current_user.lubricentro_id,
            func.lower(ClientModel.email) == email_lower
        ).first()
        
        if client_with_email:
            # Si hay cliente seleccionado, verificar que sea el mismo
            if data.cliente_id and client_with_email.id == data.cliente_id:
                pass  # OK, es el mismo cliente
            else:
                conflicts.append(ConflictDetail(
                    tipo="email",
                    valor=data.email,
                    cliente_existente=client_with_email.nombre,
                    cliente_id=client_with_email.id
                ))
    
    # Validar patentes
    if data.patentes:
        for patente in data.patentes:
            if patente and patente.strip():
                patente_lower = patente.strip().lower()
                # Buscar vehículo con esa patente
                vehicle_with_patente = db.query(VehicleModel).join(ClientModel).filter(
                    ClientModel.lubricentro_id == current_user.lubricentro_id,
                    func.lower(VehicleModel.patente) == patente_lower
                ).first()
                
                if vehicle_with_patente:
                    owner = vehicle_with_patente.cliente
                    # Si hay cliente seleccionado, verificar que sea el mismo
                    if data.cliente_id and owner.id == data.cliente_id:
                        pass  # OK, es el mismo cliente
                    else:
                        conflicts.append(ConflictDetail(
                            tipo="patente",
                            valor=patente.upper(),
                            cliente_existente=owner.nombre,
                            cliente_id=owner.id
                        ))
    
    if conflicts:
        # Generar mensaje de error
        msgs = []
        for c in conflicts:
            if c.tipo == "email":
                msgs.append(f"El email '{c.valor}' ya pertenece a {c.cliente_existente}")
            else:
                msgs.append(f"La patente '{c.valor}' ya pertenece a {c.cliente_existente}")
        
        return ValidateResponse(
            valid=False,
            conflicts=conflicts,
            message=". ".join(msgs) + ". Seleccione el cliente correcto del buscador."
        )
    
    return ValidateResponse(valid=True, conflicts=[], message=None)
