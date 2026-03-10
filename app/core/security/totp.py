"""
Autenticación de Dos Factores (2FA) con TOTP
Implementa Time-based One-Time Password según RFC 6238
"""

import pyotp
import secrets
import json
import base64
from typing import List, Tuple, Optional
from datetime import datetime


class TOTPManager:
    """
    Gestor de autenticación TOTP (Time-based One-Time Password).
    
    Uso:
        totp = TOTPManager()
        
        # Configurar 2FA para un usuario
        secret, uri = totp.generate_secret("usuario@email.com", "GestionDeTaller")
        
        # Verificar código
        if totp.verify_code(secret, "123456"):
            print("Código válido!")
    """
    
    def __init__(self, digits: int = 6, interval: int = 30):
        """
        Args:
            digits: Cantidad de dígitos del código (default: 6)
            interval: Segundos de validez del código (default: 30)
        """
        self.digits = digits
        self.interval = interval
    
    def generate_secret(self, email: str, issuer: str = "GestionDeTaller") -> Tuple[str, str]:
        """
        Generar secreto TOTP y URI para QR code.
        
        Args:
            email: Email del usuario (para identificación en la app)
            issuer: Nombre de la aplicación
            
        Returns:
            Tuple[secret, provisioning_uri]
        """
        # Generar secreto aleatorio de 32 caracteres base32
        secret = pyotp.random_base32()
        
        # Crear URI para provisioning (QR code)
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        uri = totp.provisioning_uri(name=email, issuer_name=issuer)
        
        return secret, uri
    
    def verify_code(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verificar código TOTP.
        
        Args:
            secret: Secreto TOTP del usuario
            code: Código ingresado por el usuario
            valid_window: Ventana de códigos válidos (1 = código actual ± 1)
            
        Returns:
            True si el código es válido
        """
        if not secret or not code:
            return False
        
        try:
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
            return totp.verify(code, valid_window=valid_window)
        except Exception:
            return False
    
    def get_current_code(self, secret: str) -> str:
        """
        Obtener código actual (solo para testing/debug).
        """
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        return totp.now()
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generar códigos de backup para recuperación.
        
        Args:
            count: Cantidad de códigos a generar
            
        Returns:
            Lista de códigos de 8 caracteres
        """
        codes = []
        for _ in range(count):
            # Código de 8 caracteres alfanuméricos
            code = secrets.token_hex(4).upper()
            # Formato: XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes
    
    def verify_backup_code(self, stored_codes: str, code: str) -> Tuple[bool, str]:
        """
        Verificar y consumir código de backup.
        
        Args:
            stored_codes: JSON de códigos almacenados
            code: Código a verificar
            
        Returns:
            Tuple[es_válido, códigos_actualizados_json]
        """
        try:
            codes = json.loads(stored_codes) if stored_codes else []
        except json.JSONDecodeError:
            return False, stored_codes
        
        # Normalizar código (quitar guiones, mayúsculas)
        normalized = code.replace("-", "").upper()
        
        for stored in codes:
            stored_normalized = stored.replace("-", "").upper()
            if stored_normalized == normalized:
                # Código válido - removerlo
                codes.remove(stored)
                return True, json.dumps(codes)
        
        return False, stored_codes


def encrypt_totp_secret(secret: str, encryption_key: str) -> str:
    """
    Encriptar secreto TOTP antes de almacenar en DB.
    Usa XOR simple + base64 (en producción usar Fernet de cryptography).
    
    Args:
        secret: Secreto TOTP en texto plano
        encryption_key: Clave de encriptación (usar SECRET_KEY)
    """
    # En producción, usar cryptography.fernet
    # Esta es una implementación simple para desarrollo
    key_bytes = encryption_key.encode()[:32].ljust(32, b'\0')
    secret_bytes = secret.encode()
    
    # XOR con la clave
    encrypted = bytes(a ^ b for a, b in zip(secret_bytes, key_bytes * (len(secret_bytes) // len(key_bytes) + 1)))
    
    return base64.b64encode(encrypted).decode()


def decrypt_totp_secret(encrypted: str, encryption_key: str) -> str:
    """
    Desencriptar secreto TOTP desde DB.
    """
    key_bytes = encryption_key.encode()[:32].ljust(32, b'\0')
    encrypted_bytes = base64.b64decode(encrypted.encode())
    
    # XOR inverso
    decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_bytes * (len(encrypted_bytes) // len(key_bytes) + 1)))
    
    return decrypted.decode()


# Instancia global
totp_manager = TOTPManager()
