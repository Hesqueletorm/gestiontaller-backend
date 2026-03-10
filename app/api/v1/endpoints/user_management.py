# Endpoints para gestión de usuarios por parte del Administrador
# Solo roles 0 (Desarrollador) y 1 (Administrador) tienen acceso

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.crud_user import user as crud_user
from app.models.user import User, UserRole
from app.schemas.user import (
    UserListResponse,
    UserListItem,
    UserAdminUpdate,
    User as UserSchema
)

router = APIRouter()


@router.get("/usuarios", response_model=UserListResponse)
def listar_usuarios_lubricentro(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Listar todos los usuarios APROBADOS del lubricentro del administrador.
    Solo Desarrollador (rol=0) y Administrador (rol=1) tienen acceso.
    """
    if current_user.lubricentro_id is None:
        raise HTTPException(
            status_code=400,
            detail="No pertenecés a ningún lubricentro"
        )
    
    usuarios = crud_user.get_users_by_lubricentro(
        db, lubricentro_id=current_user.lubricentro_id
    )
    
    # Filtrar solo usuarios aprobados
    usuarios_aprobados = [u for u in usuarios if getattr(u, 'aprobado', True)]
    
    # Convertir a schema con nombre de rol
    usuarios_list = []
    for u in usuarios_aprobados:
        usuarios_list.append(UserListItem(
            id=u.id,
            usuario=u.usuario,
            email=u.email,
            nombre=u.nombre,
            rol=u.rol,
            rol_nombre=UserRole.get_nombre(u.rol),
            activo=u.activo,
            aprobado=getattr(u, 'aprobado', True),
            fecha_creacion=u.fecha_creacion
        ))
    
    return UserListResponse(
        usuarios=usuarios_list,
        total=len(usuarios_list)
    )


@router.get("/solicitudes-pendientes", response_model=UserListResponse)
def listar_solicitudes_pendientes(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Listar usuarios pendientes de aprobación en el lubricentro.
    Estos son usuarios que se registraron para unirse al lubricentro
    pero aún no fueron aprobados por el administrador.
    """
    if current_user.lubricentro_id is None:
        raise HTTPException(
            status_code=400,
            detail="No pertenecés a ningún lubricentro"
        )
    
    usuarios = crud_user.get_users_by_lubricentro(
        db, lubricentro_id=current_user.lubricentro_id
    )
    
    # Filtrar solo usuarios NO aprobados (pendientes)
    usuarios_pendientes = [u for u in usuarios if not getattr(u, 'aprobado', True)]
    
    # Convertir a schema
    usuarios_list = []
    for u in usuarios_pendientes:
        usuarios_list.append(UserListItem(
            id=u.id,
            usuario=u.usuario,
            email=u.email,
            nombre=u.nombre,
            rol=u.rol,
            rol_nombre=UserRole.get_nombre(u.rol),
            activo=u.activo,
            aprobado=False,
            fecha_creacion=u.fecha_creacion
        ))
    
    return UserListResponse(
        usuarios=usuarios_list,
        total=len(usuarios_list)
    )


@router.post("/solicitudes/{user_id}/aprobar")
def aprobar_solicitud(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Aprobar la solicitud de un usuario para unirse al lubricentro.
    """
    usuario = crud_user.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(
            status_code=403,
            detail="No podés aprobar usuarios de otro lubricentro"
        )
    
    if getattr(usuario, 'aprobado', True):
        raise HTTPException(
            status_code=400,
            detail="Este usuario ya está aprobado"
        )
    
    # Aprobar usuario
    usuario.aprobado = True
    usuario.activo = True
    db.add(usuario)
    db.commit()
    
    return {
        "success": True, 
        "message": f"Usuario {usuario.usuario} aprobado exitosamente. Ya puede iniciar sesión."
    }


@router.post("/solicitudes/{user_id}/rechazar")
def rechazar_solicitud(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Rechazar y eliminar la solicitud de un usuario.
    """
    usuario = crud_user.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(
            status_code=403,
            detail="No podés rechazar usuarios de otro lubricentro"
        )
    
    if getattr(usuario, 'aprobado', True):
        raise HTTPException(
            status_code=400,
            detail="No podés rechazar un usuario ya aprobado. Usá desactivar."
        )
    
    # Eliminar usuario rechazado
    nombre_usuario = usuario.usuario
    db.delete(usuario)
    db.commit()
    
    return {
        "success": True, 
        "message": f"Solicitud de {nombre_usuario} rechazada y eliminada."
    }


@router.put("/usuarios/{user_id}", response_model=UserSchema)
def actualizar_usuario(
    user_id: int,
    user_update: UserAdminUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Actualizar rol o datos de un usuario del lubricentro.
    El Administrador solo puede asignar roles Coordinador (2) o Operador (3).
    No puede modificar otros Administradores ni al Desarrollador.
    """
    # Obtener usuario a modificar
    usuario = crud_user.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que el usuario pertenece al mismo lubricentro
    if usuario.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(
            status_code=403,
            detail="No podés modificar usuarios de otro lubricentro"
        )
    
    # Verificar que no se está intentando modificar a sí mismo
    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="No podés modificar tu propio rol desde acá"
        )
    
    # Verificar que no se está modificando a un Desarrollador o Administrador
    if usuario.rol in [UserRole.DESARROLLADOR, UserRole.ADMINISTRADOR]:
        raise HTTPException(
            status_code=403,
            detail="No podés modificar a Desarrolladores o Administradores"
        )
    
    # Validar el rol que se quiere asignar (solo Coordinador o Operador)
    if user_update.rol is not None:
        if user_update.rol not in [UserRole.COORDINADOR, UserRole.OPERADOR]:
            raise HTTPException(
                status_code=400,
                detail="Solo podés asignar roles Coordinador (2) o Operador (3)"
            )
    
    # Actualizar solo los campos proporcionados
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    
    return usuario


@router.delete("/usuarios/{user_id}")
def desactivar_usuario(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Desactivar un usuario del lubricentro (no elimina, solo marca como inactivo).
    No se puede desactivar al Desarrollador ni a otros Administradores.
    """
    # Obtener usuario
    usuario = crud_user.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar mismo lubricentro
    if usuario.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(
            status_code=403,
            detail="No podés desactivar usuarios de otro lubricentro"
        )
    
    # Verificar que no se está desactivando a sí mismo
    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="No podés desactivarte a vos mismo"
        )
    
    # Verificar que no se está desactivando a un Dev o Admin
    if usuario.rol in [UserRole.DESARROLLADOR, UserRole.ADMINISTRADOR]:
        raise HTTPException(
            status_code=403,
            detail="No podés desactivar a Desarrolladores o Administradores"
        )
    
    # Desactivar usuario
    usuario.activo = False
    db.add(usuario)
    db.commit()
    
    return {"success": True, "message": f"Usuario {usuario.usuario} desactivado"}


@router.post("/usuarios/{user_id}/activar")
def activar_usuario(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Reactivar un usuario previamente desactivado.
    """
    # Obtener usuario
    usuario = crud_user.get(db, id=user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar mismo lubricentro
    if usuario.lubricentro_id != current_user.lubricentro_id:
        raise HTTPException(
            status_code=403,
            detail="No podés activar usuarios de otro lubricentro"
        )
    
    # Activar usuario
    usuario.activo = True
    db.add(usuario)
    db.commit()
    
    return {"success": True, "message": f"Usuario {usuario.usuario} activado"}
