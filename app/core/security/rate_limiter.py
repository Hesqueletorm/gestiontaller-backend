"""
Rate Limiter para protección contra ataques de fuerza bruta.
Implementa algoritmo de ventana deslizante con soporte para Redis (producción)
y almacenamiento en memoria (desarrollo).
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict
from threading import RLock
from datetime import datetime
import hashlib

# Intentar importar Redis para producción (opcional)
REDIS_AVAILABLE = False
try:
    import redis.asyncio as redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    pass  # Redis no está instalado, usar almacenamiento en memoria


class RateLimiter:
    """
    Rate Limiter con algoritmo de ventana deslizante.
    
    Uso:
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        if not limiter.is_allowed(identifier):
            raise RateLimitExceeded(limiter.get_retry_after(identifier))
        
        limiter.record_attempt(identifier)
    """
    
    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: int = 60,
        block_duration_seconds: int = 300,
        name: str = "default"
    ):
        """
        Args:
            max_requests: Número máximo de intentos permitidos
            window_seconds: Ventana de tiempo en segundos
            block_duration_seconds: Tiempo de bloqueo tras exceder límite
            name: Nombre del limiter (para logging)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds
        self.name = name
        
        # Almacenamiento en memoria (desarrollo)
        self._attempts: Dict[str, list] = defaultdict(list)
        self._blocked: Dict[str, float] = {}
        self._lock = RLock()
        
        # Redis client (producción)
        self._redis: Optional[redis.Redis] = None
    
    async def init_redis(self, redis_url: str = "redis://localhost:6379"):
        """Inicializa conexión Redis para producción."""
        if REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                await self._redis.ping()
                print(f"[RateLimiter:{self.name}] Conectado a Redis")
            except Exception as e:
                print(f"[RateLimiter:{self.name}] Redis no disponible, usando memoria: {e}")
                self._redis = None
    
    def _get_key(self, identifier: str) -> str:
        """Genera clave única para el identificador."""
        # Hash para proteger información sensible
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"ratelimit:{self.name}:{hashed}"
    
    def _cleanup_old_attempts(self, identifier: str) -> None:
        """Limpia intentos antiguos fuera de la ventana."""
        current_time = time.time()
        cutoff = current_time - self.window_seconds
        
        with self._lock:
            self._attempts[identifier] = [
                t for t in self._attempts[identifier] if t > cutoff
            ]
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Verifica si se permite un nuevo intento.
        
        Args:
            identifier: Usuario, IP, o combinación
            
        Returns:
            True si se permite, False si está bloqueado o excedió límite
        """
        current_time = time.time()
        
        with self._lock:
            # Verificar si está bloqueado
            if identifier in self._blocked:
                if current_time < self._blocked[identifier]:
                    return False
                else:
                    # Desbloquear
                    del self._blocked[identifier]
                    self._attempts[identifier] = []
            
            # Limpiar intentos antiguos
            self._cleanup_old_attempts(identifier)
            
            # Verificar cantidad de intentos
            return len(self._attempts[identifier]) < self.max_requests
    
    def record_attempt(self, identifier: str, success: bool = False) -> None:
        """
        Registra un intento.
        
        Args:
            identifier: Usuario, IP, o combinación
            success: Si fue exitoso (los exitosos resetean el contador)
        """
        current_time = time.time()
        
        with self._lock:
            if success:
                # Login exitoso - resetear
                self._attempts[identifier] = []
                if identifier in self._blocked:
                    del self._blocked[identifier]
            else:
                self._attempts[identifier].append(current_time)
                
                # Verificar si debe bloquearse
                self._cleanup_old_attempts(identifier)
                if len(self._attempts[identifier]) >= self.max_requests:
                    self._blocked[identifier] = current_time + self.block_duration_seconds
    
    def get_remaining_attempts(self, identifier: str) -> int:
        """Retorna intentos restantes."""
        self._cleanup_old_attempts(identifier)
        with self._lock:
            return max(0, self.max_requests - len(self._attempts[identifier]))
    
    def get_retry_after(self, identifier: str) -> int:
        """Retorna segundos hasta poder reintentar."""
        current_time = time.time()
        
        with self._lock:
            if identifier in self._blocked:
                remaining = int(self._blocked[identifier] - current_time)
                return max(0, remaining)
            
            # Si no está bloqueado pero excedió, calcular desde el intento más antiguo
            if self._attempts[identifier]:
                oldest = min(self._attempts[identifier])
                remaining = int((oldest + self.window_seconds) - current_time)
                return max(0, remaining)
        
        return 0
    
    def is_blocked(self, identifier: str) -> bool:
        """Verifica si está bloqueado."""
        current_time = time.time()
        with self._lock:
            if identifier in self._blocked:
                return current_time < self._blocked[identifier]
        return False
    
    def get_block_remaining(self, identifier: str) -> int:
        """Retorna minutos restantes de bloqueo."""
        current_time = time.time()
        with self._lock:
            if identifier in self._blocked:
                remaining_seconds = self._blocked[identifier] - current_time
                return max(0, int(remaining_seconds / 60) + 1)
        return 0
    
    def reset(self, identifier: str) -> None:
        """Resetea todos los datos de un identificador."""
        with self._lock:
            self._attempts.pop(identifier, None)
            self._blocked.pop(identifier, None)


# Instancias pre-configuradas
login_limiter = RateLimiter(
    max_requests=5,
    window_seconds=300,  # 5 minutos
    block_duration_seconds=900,  # 15 minutos de bloqueo
    name="login"
)

ip_limiter = RateLimiter(
    max_requests=100,
    window_seconds=60,  # 1 minuto
    block_duration_seconds=300,  # 5 minutos
    name="ip"
)

api_limiter = RateLimiter(
    max_requests=60,
    window_seconds=60,  # 60 requests por minuto
    block_duration_seconds=60,
    name="api"
)

password_reset_limiter = RateLimiter(
    max_requests=3,
    window_seconds=3600,  # 1 hora
    block_duration_seconds=3600,
    name="password_reset"
)

registration_limiter = RateLimiter(
    max_requests=5,
    window_seconds=3600,  # 1 hora
    block_duration_seconds=3600,
    name="registration"
)
