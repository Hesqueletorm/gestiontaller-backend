"""
Utilidades compartidas para autenticación
"""
from datetime import datetime, timedelta
from typing import Any, Dict
import random
import string

# Almacenamiento temporal de códigos pendientes
# En producción, usar Redis o base de datos
codigos_pendientes: Dict[str, Dict[str, Any]] = {}
codigos_recuperacion: Dict[str, Dict[str, Any]] = {}


def generar_codigo() -> str:
    """Genera un código de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))


def limpiar_codigos_expirados():
    """Limpia códigos que hayan expirado (>10 minutos)"""
    ahora = datetime.now()
    emails_a_eliminar = [
        email for email, datos in codigos_pendientes.items()
        if (ahora - datos['timestamp']) > timedelta(minutes=10)
    ]
    for email in emails_a_eliminar:
        del codigos_pendientes[email]


def limpiar_codigos_recuperacion_expirados():
    """Limpia códigos de recuperación que hayan expirado (>10 minutos)"""
    ahora = datetime.now()
    emails_a_eliminar = [
        email for email, datos in codigos_recuperacion.items()
        if (ahora - datos['timestamp']) > timedelta(minutes=10)
    ]
    for email in emails_a_eliminar:
        del codigos_recuperacion[email]
