# Inicialización de base de datos
# Crea las tablas y el usuario admin por defecto

from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.base import Base
from app.models.user import User
from app.models.lubricentro import Lubricentro
from app.core.auth import get_password_hash


def init_db() -> None:
    """Crear todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)


def create_default_lubricentro(db: Session) -> Lubricentro:
    """Crear lubricentro por defecto si no existe"""
    existing = db.query(Lubricentro).filter(Lubricentro.codigo == "DEMO001").first()
    
    if not existing:
        lubricentro = Lubricentro(
            nombre="Lubricentro Demo",
            codigo="DEMO001",
            activo=True,
        )
        db.add(lubricentro)
        db.commit()
        db.refresh(lubricentro)
        print("[init_db] Lubricentro Demo creado exitosamente")
        return lubricentro
    
    print("[init_db] Lubricentro Demo ya existe")
    return existing


def create_default_user(db: Session) -> None:
    """Crear usuario admin por defecto si no existe"""
    # Primero asegurar que existe el lubricentro demo
    lubricentro = create_default_lubricentro(db)
    
    # Verificar si ya existe el usuario admin
    existing_user = db.query(User).filter(User.usuario == "admin").first()
    
    if not existing_user:
        admin_user = User(
            usuario="admin",
            password=get_password_hash("qwe123qwe"),
            email="admin@lubricentrom.local",
            nombre="Desarrollador",
            activo=True,
            email_verificado=True,
            rol=0,  # 0 = Desarrollador (acceso total incluido Herramientas Dev)
            lubricentro_id=lubricentro.id,  # Asignar lubricentro para que funcione todo
        )
        db.add(admin_user)
        db.commit()
        print("[init_db] Usuario admin creado exitosamente")
    else:
        # Si el admin existe pero no tiene lubricentro, asignarlo
        if not existing_user.lubricentro_id:
            existing_user.lubricentro_id = lubricentro.id
            db.commit()
            print("[init_db] Lubricentro asignado al usuario admin")
        else:
            print("[init_db] Usuario admin ya existe")


def init_all(db: Session) -> None:
    """Inicializar base de datos completa"""
    init_db()
    create_default_user(db)
