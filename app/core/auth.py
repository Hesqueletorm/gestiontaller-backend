from datetime import datetime, timedelta
from typing import Optional, Union, Any, Set
import secrets
import hashlib

from jose import jwt
import bcrypt

from app.core.config import settings

# ============== BCRYPT DIRECTO (máxima seguridad) ==============
# Rounds 14 = ~1 segundo por hash (buena protección contra fuerza bruta)
# Rounds 12 = ~250ms, Rounds 10 = ~60ms
BCRYPT_ROUNDS = 14  # Factor de trabajo alto para máxima seguridad
ALGORITHM = "HS256"


# ============== TOKEN BLACKLIST ==============
# En producción, usar Redis para persistencia y escalabilidad
class TokenBlacklist:
    """
    Blacklist de tokens para invalidar sesiones (logout seguro).
    En memoria para desarrollo, Redis recomendado para producción.
    """
    def __init__(self):
        self._blacklist: Set[str] = set()
        self._jti_blacklist: Set[str] = set()  # JWT ID blacklist
    
    def add_token(self, token: str) -> None:
        """Agregar token completo a la blacklist"""
        # Guardar hash del token para no almacenar el token en texto
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self._blacklist.add(token_hash)
    
    def add_jti(self, jti: str) -> None:
        """Agregar JWT ID a la blacklist (más eficiente)"""
        self._jti_blacklist.add(jti)
    
    def is_blacklisted(self, token: str) -> bool:
        """Verificar si un token está en la blacklist"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in self._blacklist
    
    def is_jti_blacklisted(self, jti: str) -> bool:
        """Verificar si un JTI está en la blacklist"""
        return jti in self._jti_blacklist
    
    def cleanup_expired(self) -> None:
        """Limpiar tokens expirados (llamar periódicamente)"""
        # En una implementación con Redis, usar TTL automático
        pass

# Instancia global
token_blacklist = TokenBlacklist()


def generate_jti() -> str:
    """Generar un JWT ID único para cada token"""
    return secrets.token_urlsafe(32)


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    fresh: bool = False
) -> str:
    """
    Crear access token con JTI para blacklisting.
    
    Args:
        subject: ID del usuario
        expires_delta: Tiempo de expiración
        fresh: True si es un login reciente (para operaciones sensibles)
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = generate_jti()
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": jti,
        "fresh": fresh,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crear refresh token con JTI para rotación y blacklisting.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    jti = generate_jti()
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": jti,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar contraseña con bcrypt.
    Solo acepta hashes bcrypt válidos.
    """
    if not hashed_password:
        return False
    
    # Solo aceptar hashes bcrypt válidos
    if not hashed_password.startswith(('$2b$', '$2a$', '$2y$')):
        return False
    
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hashear contraseña con bcrypt (máxima seguridad)"""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    ).decode('utf-8')


def verify_token_not_blacklisted(token: str, payload: dict) -> bool:
    """
    Verificar que un token no esté en la blacklist.
    Retorna True si el token es válido (no blacklisted).
    """
    # Verificar por JTI (más eficiente)
    jti = payload.get("jti")
    if jti and token_blacklist.is_jti_blacklisted(jti):
        return False
    
    # Verificar token completo (fallback)
    if token_blacklist.is_blacklisted(token):
        return False
    
    return True


def blacklist_token(token: str, payload: dict = None) -> None:
    """
    Agregar token a la blacklist (para logout).
    """
    if payload and "jti" in payload:
        token_blacklist.add_jti(payload["jti"])
    else:
        token_blacklist.add_token(token)


def is_token_fresh(payload: dict) -> bool:
    """
    Verificar si un token es 'fresh' (login reciente).
    Útil para operaciones sensibles como cambio de contraseña.
    """
    return payload.get("fresh", False)

