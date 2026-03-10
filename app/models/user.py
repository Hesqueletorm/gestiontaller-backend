# Modelos SQLAlchemy para LubricentroM
# Compatibles con el esquema de lubricentroMal (SQLite)

from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class UserRole:
    """
    Constantes de roles del sistema.
    
    - DESARROLLADOR (0): Solo usuario 'admin', acceso total incluyendo DevTools
    - ADMINISTRADOR (1): Dueño del lubricentro, gestiona usuarios
    - COORDINADOR (2): Supervisor, acceso a todo menos gestión de usuarios
    - OPERADOR (3): Empleado, sin acceso a Configuraciones
    """
    DESARROLLADOR = 0
    ADMINISTRADOR = 1
    COORDINADOR = 2
    OPERADOR = 3
    
    @classmethod
    def get_nombre(cls, rol_id: int) -> str:
        """Devuelve el nombre del rol según su ID"""
        nombres = {
            cls.DESARROLLADOR: "Desarrollador",
            cls.ADMINISTRADOR: "Administrador",
            cls.COORDINADOR: "Coordinador",
            cls.OPERADOR: "Operador"
        }
        return nombres.get(rol_id, "Desconocido")


class User(Base):
    """
    Tabla: usuarios
    Modelo compatible con lubricentroMal
    Multi-tenant: usuarios pertenecen a un lubricentro
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario = Column(String, nullable=False, index=True)  # username (único por lubricentro)
    password = Column(String, nullable=False)  # hashed password
    email = Column(String, nullable=True, index=True)
    fecha_creacion = Column(DateTime, server_default=func.now())
    activo = Column(Boolean, default=True)
    email_verificado = Column(Boolean, default=True)
    rol = Column(Integer, default=UserRole.OPERADOR)  # 0=Dev, 1=Admin, 2=Coord, 3=Oper
    nombre = Column(String, nullable=True)
    imagen = Column(String, nullable=True)  # Avatar/profile image path
    
    # Multi-tenant: Relación con Lubricentro
    lubricentro_id = Column(Integer, ForeignKey("lubricentros.id", ondelete="CASCADE"), nullable=True, index=True)
    lubricentro = relationship("Lubricentro", back_populates="usuarios")
    
    # Sistema de aprobación: usuarios que se unen a lubricentro existente quedan pendientes
    aprobado = Column(Boolean, default=True)  # False = pendiente de aprobación por admin
    
    # ============== SEGURIDAD: Bloqueo de cuenta ==============
    failed_login_attempts = Column(Integer, default=0)  # Intentos fallidos consecutivos
    locked_until = Column(DateTime, nullable=True)  # Fecha hasta la que está bloqueada
    last_login_at = Column(DateTime, nullable=True)  # Último login exitoso
    last_login_ip = Column(String, nullable=True)  # IP del último login
    last_failed_login = Column(DateTime, nullable=True)  # Último intento fallido
    password_changed_at = Column(DateTime, nullable=True)  # Última vez que cambió contraseña
    
    # ============== 2FA/TOTP ==============
    totp_secret = Column(String, nullable=True)  # Secreto TOTP encriptado
    totp_enabled = Column(Boolean, default=False)  # Si tiene 2FA activado
    totp_backup_codes = Column(Text, nullable=True)  # Códigos de backup (JSON encriptado)
    
    # Configuración visual personalizada del usuario (puede sobreescribir la del lubricentro)
    color_fondo = Column(String, default=None)  # Si es None, usa el del lubricentro
    color_tematica = Column(String, default=None)
    color_tematica2 = Column(String, default=None)
    color_letras = Column(String, default=None)
    tema = Column(String, default=None)
    idioma = Column(String, default="Español")
    # Colores de la barra de identidad (gradiente 3 colores)
    color_identidad1 = Column(String, default=None)
    color_identidad2 = Column(String, default=None)
    color_identidad3 = Column(String, default=None)
    
    # Comentario del administrador de maldonadomaster
    comentario_admin = Column(Text, nullable=True)  # Notas/comentarios sobre el usuario
    
    def is_locked(self) -> bool:
        """Verificar si la cuenta está bloqueada"""
        if self.locked_until is None:
            return False
        from datetime import datetime
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, minutes: int = 30) -> None:
        """Bloquear la cuenta por X minutos"""
        from datetime import datetime, timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
    
    def unlock_account(self) -> None:
        """Desbloquear la cuenta"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_failed_login(self) -> None:
        """Registrar un intento de login fallido"""
        from datetime import datetime
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        self.last_failed_login = datetime.utcnow()
    
    def record_successful_login(self, ip_address: str = None) -> None:
        """Registrar un login exitoso"""
        from datetime import datetime
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address

