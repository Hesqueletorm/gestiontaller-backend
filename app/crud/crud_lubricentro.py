# CRUD para Lubricentros

from typing import List, Optional
import random
import string
from sqlalchemy.orm import Session

from app.models.lubricentro import Lubricentro


def generar_codigo_unico(db: Session, longitud: int = 8) -> str:
    """Genera un código único para el lubricentro"""
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))
        existing = db.query(Lubricentro).filter(Lubricentro.codigo == codigo).first()
        if not existing:
            return codigo


def crear_lubricentro(
    db: Session,
    nombre: str,
    color_fondo: str = "#04060c",
    color_tematica: str = "#f2e71a",
    color_tematica2: str = "#FFA000",
    color_letras: str = "#F5F7FA",
    tema: str = "dark",
    activo: bool = False  # Por defecto inactivo hasta que sea aprobado
) -> Lubricentro:
    """Crea un nuevo lubricentro (inactivo por defecto, pendiente de aprobación)"""
    codigo = generar_codigo_unico(db)
    
    db_lubricentro = Lubricentro(
        nombre=nombre,
        codigo=codigo,
        color_fondo=color_fondo,
        color_tematica=color_tematica,
        color_tematica2=color_tematica2,
        color_letras=color_letras,
        tema=tema,
        activo=activo  # Pendiente de aprobación
    )
    db.add(db_lubricentro)
    db.commit()
    db.refresh(db_lubricentro)
    return db_lubricentro


def obtener_lubricentro(db: Session, lubricentro_id: int) -> Optional[Lubricentro]:
    """Obtiene un lubricentro por ID"""
    return db.query(Lubricentro).filter(Lubricentro.id == lubricentro_id).first()


def obtener_lubricentro_por_codigo(db: Session, codigo: str) -> Optional[Lubricentro]:
    """Obtiene un lubricentro por código"""
    return db.query(Lubricentro).filter(Lubricentro.codigo == codigo).first()


def listar_lubricentros(db: Session, solo_activos: bool = True) -> List[Lubricentro]:
    """Lista todos los lubricentros"""
    query = db.query(Lubricentro)
    if solo_activos:
        query = query.filter(Lubricentro.activo == True)
    return query.order_by(Lubricentro.nombre).all()


def actualizar_lubricentro(
    db: Session,
    lubricentro_id: int,
    **kwargs
) -> Optional[Lubricentro]:
    """Actualiza un lubricentro"""
    db_lubricentro = obtener_lubricentro(db, lubricentro_id)
    if not db_lubricentro:
        return None
    
    for key, value in kwargs.items():
        if hasattr(db_lubricentro, key) and value is not None:
            setattr(db_lubricentro, key, value)
    
    db.commit()
    db.refresh(db_lubricentro)
    return db_lubricentro


def desactivar_lubricentro(db: Session, lubricentro_id: int) -> bool:
    """Desactiva un lubricentro (soft delete)"""
    db_lubricentro = obtener_lubricentro(db, lubricentro_id)
    if not db_lubricentro:
        return False
    
    db_lubricentro.activo = False
    db.commit()
    return True


def get_all_active(db: Session) -> List[Lubricentro]:
    """Obtiene todos los lubricentros activos para el registro"""
    return db.query(Lubricentro).filter(Lubricentro.activo == True).order_by(Lubricentro.nombre).all()


# Instancia del CRUD
lubricentro = type('LubricentroCRUD', (), {
    'crear': staticmethod(crear_lubricentro),
    'obtener': staticmethod(obtener_lubricentro),
    'obtener_por_codigo': staticmethod(obtener_lubricentro_por_codigo),
    'listar': staticmethod(listar_lubricentros),
    'actualizar': staticmethod(actualizar_lubricentro),
    'desactivar': staticmethod(desactivar_lubricentro),
    'generar_codigo': staticmethod(generar_codigo_unico),
    'get_all_active': staticmethod(get_all_active),
})()
