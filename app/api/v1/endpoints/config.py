# Endpoint para configuración del usuario (multi-tenant)
# Permite obtener y actualizar la configuración visual del usuario

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api import deps
from app.models.user import User
from app.models.lubricentro import Lubricentro
from app.schemas.user import UserConfig, UserConfigUpdate
from app.crud.crud_lubricentro import lubricentro as crud_lubricentro

router = APIRouter()


@router.get("/me", response_model=UserConfig)
def get_my_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener configuración del lubricentro del usuario actual.
    La configuración es compartida por todos los usuarios del mismo lubricentro.
    """
    # Valores por defecto
    defaults = {
        "nombre": "Mi Lubricentro",
        "codigo": None,
        "color_fondo": "#04060c",
        "color_tematica": "#f2e71a",
        "color_tematica2": "#FFA000",
        "color_letras": "#F5F7FA",
        "tema": "dark",
        "idioma": "Español",
        "color_identidad1": "#FFA000",
        "color_identidad2": "#FBF7E3",
        "color_identidad3": "#0F172A",
        "peso_identidad1": 33,
        "peso_identidad2": 34,
        "peso_identidad3": 33,
    }
    
    if not current_user.lubricentro_id:
        # Usuario sin lubricentro, devolver defaults
        return UserConfig(
            lubricentro_id=None,
            lubricentro_nombre=defaults["nombre"],
            lubricentro_codigo=defaults["codigo"],
            color_fondo=defaults["color_fondo"],
            color_tematica=defaults["color_tematica"],
            color_tematica2=defaults["color_tematica2"],
            color_letras=defaults["color_letras"],
            tema=defaults["tema"],
            idioma=defaults["idioma"],
            color_identidad1=defaults["color_identidad1"],
            color_identidad2=defaults["color_identidad2"],
            color_identidad3=defaults["color_identidad3"],
            peso_identidad1=defaults["peso_identidad1"],
            peso_identidad2=defaults["peso_identidad2"],
            peso_identidad3=defaults["peso_identidad3"],
        )
    
    # Obtener configuración del lubricentro
    lubricentro = crud_lubricentro.obtener(db, current_user.lubricentro_id)
    if not lubricentro:
        raise HTTPException(status_code=404, detail="Lubricentro no encontrado")
    
    return UserConfig(
        lubricentro_id=lubricentro.id,
        lubricentro_nombre=lubricentro.nombre or defaults["nombre"],
        lubricentro_codigo=lubricentro.codigo,
        color_fondo=lubricentro.color_fondo or defaults["color_fondo"],
        color_tematica=lubricentro.color_tematica or defaults["color_tematica"],
        color_tematica2=lubricentro.color_tematica2 or defaults["color_tematica2"],
        color_letras=lubricentro.color_letras or defaults["color_letras"],
        tema=lubricentro.tema or defaults["tema"],
        idioma=lubricentro.idioma or defaults["idioma"],
        color_identidad1=getattr(lubricentro, 'color_identidad1', None) or defaults["color_identidad1"],
        color_identidad2=getattr(lubricentro, 'color_identidad2', None) or defaults["color_identidad2"],
        color_identidad3=getattr(lubricentro, 'color_identidad3', None) or defaults["color_identidad3"],
        peso_identidad1=getattr(lubricentro, 'peso_identidad1', None) or defaults["peso_identidad1"],
        peso_identidad2=getattr(lubricentro, 'peso_identidad2', None) or defaults["peso_identidad2"],
        peso_identidad3=getattr(lubricentro, 'peso_identidad3', None) or defaults["peso_identidad3"],
    )


@router.put("/me", response_model=UserConfig)
def update_my_config(
    config_in: UserConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Actualizar configuración del lubricentro.
    La configuración es compartida por todos los usuarios del mismo lubricentro.
    El nombre del lubricentro solo puede ser cambiado por admin (rol=1) o desarrollador (rol=0).
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    lubricentro = crud_lubricentro.obtener(db, current_user.lubricentro_id)
    if not lubricentro:
        raise HTTPException(status_code=404, detail="Lubricentro no encontrado")
    
    # Actualizar solo los campos que vienen en el request
    update_data = config_in.model_dump(exclude_unset=True)
    
    # Mapeo de campos del request a campos del modelo Lubricentro
    field_mapping = {
        'nombre_lubricentro': 'nombre',
        'color_fondo': 'color_fondo',
        'color_tematica': 'color_tematica',
        'color_tematica2': 'color_tematica2',
        'color_letras': 'color_letras',
        'tema': 'tema',
        'idioma': 'idioma',
        'color_identidad1': 'color_identidad1',
        'color_identidad2': 'color_identidad2',
        'color_identidad3': 'color_identidad3',
        'peso_identidad1': 'peso_identidad1',
        'peso_identidad2': 'peso_identidad2',
        'peso_identidad3': 'peso_identidad3',
    }
    
    for request_field, model_field in field_mapping.items():
        if request_field in update_data:
            value = update_data[request_field]
            # Solo admin o dev pueden cambiar el nombre del lubricentro
            if request_field == 'nombre_lubricentro' and current_user.rol not in [0, 1]:
                continue  # Ignorar si no tiene permisos
            if hasattr(lubricentro, model_field):
                setattr(lubricentro, model_field, value)
    
    db.add(lubricentro)
    db.commit()
    db.refresh(lubricentro)
    
    # Devolver la configuración actualizada
    return get_my_config(db=db, current_user=current_user)
    
    # Re-obtener config completa
    return get_my_config(db=db, current_user=current_user)


# --- Configuración de Módulos ---
# Almacenamiento simple en memoria (en producción usar tabla de BD)
_modules_config_store = {}


@router.get("/modules")
def get_modules_config(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener configuración de módulos del usuario/lubricentro.
    """
    key = f"user_{current_user.id}"
    if current_user.lubricentro_id:
        key = f"lubricentro_{current_user.lubricentro_id}"
    
    return _modules_config_store.get(key, {"modulos": {}})


@router.put("/modules")
def update_modules_config(
    config_in: dict,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Actualizar configuración de módulos.
    """
    key = f"user_{current_user.id}"
    if current_user.lubricentro_id:
        key = f"lubricentro_{current_user.lubricentro_id}"
    
    _modules_config_store[key] = config_in
    return config_in


@router.get("/storage")
def get_storage_info(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener información de almacenamiento del lubricentro actual.
    Calcula el tamaño aproximado de los datos almacenados.
    """
    if not current_user.lubricentro_id:
        raise HTTPException(status_code=400, detail="Usuario sin lubricentro asignado")
    
    lubricentro_id = current_user.lubricentro_id
    
    # Tablas que tienen datos por lubricentro
    tables_with_lubricentro = [
        "users",
        "clientes", 
        "vehiculos",
        "turnos",
        "productos",
        "servicios",
        "facturas",
        "factura_items",
        "movimientos_stock",
        "ordenes_compra",
        "notificaciones"
    ]
    
    total_bytes = 0
    table_sizes = {}
    
    for table_name in tables_with_lubricentro:
        try:
            # Contar registros por lubricentro
            result = db.execute(
                text(f"SELECT COUNT(*) FROM {table_name} WHERE lubricentro_id = :lid"),
                {"lid": lubricentro_id}
            )
            count = result.scalar() or 0
            
            # Estimación: ~500 bytes por registro promedio
            estimated_size = count * 500
            total_bytes += estimated_size
            table_sizes[table_name] = {
                "registros": count,
                "bytes_estimados": estimated_size
            }
        except Exception:
            # La tabla puede no existir o no tener el campo lubricentro_id
            pass
    
    # Límite de almacenamiento por lubricentro (configurable, default 100MB)
    storage_limit_bytes = 100 * 1024 * 1024  # 100 MB
    
    return {
        "usado_bytes": total_bytes,
        "limite_bytes": storage_limit_bytes,
        "porcentaje_usado": round((total_bytes / storage_limit_bytes) * 100, 2) if storage_limit_bytes > 0 else 0,
        "tablas": table_sizes,
        "lubricentro_id": lubricentro_id
    }
