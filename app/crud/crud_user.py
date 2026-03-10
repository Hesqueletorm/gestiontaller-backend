# CRUD para usuarios
# Compatible con el modelo de lubricentroMal

from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from app.core.auth import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Obtener usuario por nombre de usuario (campo 'usuario')"""
        return db.query(User).filter(User.usuario == username).first()
    
    def get_by_username_and_lubricentro(
        self, db: Session, *, username: str, lubricentro_id: int
    ) -> Optional[User]:
        """Obtener usuario por nombre de usuario dentro de un lubricentro específico"""
        return db.query(User).filter(
            User.usuario == username,
            User.lubricentro_id == lubricentro_id
        ).first()
    
    def get_by_username_for_auth(
        self, db: Session, *, username: str, lubricentro_id: Optional[int] = None
    ) -> Optional[User]:
        """
        Obtener usuario para autenticación (sin verificar contraseña).
        Útil para verificar bloqueo de cuenta antes de autenticar.
        """
        if lubricentro_id:
            return self.get_by_username_and_lubricentro(db, username=username, lubricentro_id=lubricentro_id)
        return self.get_by_username(db, username=username)
    
    def get_users_by_lubricentro(self, db: Session, *, lubricentro_id: int) -> List[User]:
        """Obtener todos los usuarios de un lubricentro"""
        return db.query(User).filter(User.lubricentro_id == lubricentro_id).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Crear nuevo usuario"""
        db_obj = User(
            usuario=obj_in.usuario,
            email=obj_in.email,
            password=get_password_hash(obj_in.password),
            nombre=obj_in.nombre,
            lubricentro_id=obj_in.lubricentro_id,
            rol=obj_in.rol if obj_in.rol is not None else 0,
            activo=True,
            email_verificado=True,
            aprobado=obj_in.aprobado if obj_in.aprobado is not None else True,  # False si necesita aprobación del admin
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]) -> User:
        """Actualizar usuario existente"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password"] = hashed_password
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, username: str, password: str, lubricentro_id: Optional[int] = None) -> Optional[User]:
        """
        Autenticar usuario por nombre de usuario, contraseña y opcionalmente lubricentro.
        Si se proporciona lubricentro_id, busca específicamente en ese lubricentro.
        Si no, busca en todos (para compatibilidad hacia atrás).
        """
        if lubricentro_id:
            # Buscar usuario específico del lubricentro
            user = self.get_by_username_and_lubricentro(db, username=username, lubricentro_id=lubricentro_id)
        else:
            # Buscar por username globalmente (compatibilidad)
            user = self.get_by_username(db, username=username)
        
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Verificar si el usuario está activo"""
        return user.activo

    def is_superuser(self, user: User) -> bool:
        """Verificar si el usuario es Desarrollador"""
        return user.rol == 0


user = CRUDUser(User)
