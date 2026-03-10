"""
Validadores y Sanitizadores de entrada.
Previene SQL Injection, XSS y otras vulnerabilidades de inyección.
"""

import re
import html
import unicodedata
from typing import Optional, Tuple, Any, List
from .exceptions import InvalidInputException, SQLInjectionDetected, XSSDetected


class Sanitizer:
    """Sanitización de datos de entrada."""
    
    # Patrones de SQL Injection
    SQL_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b\s+[\d'\"]+\s*=\s*[\d'\"]+)",
        r"(\bAND\b\s+[\d'\"]+\s*=\s*[\d'\"]+)",
        r"(UNION\s+(ALL\s+)?SELECT)",
        r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
        r"(\bINTO\s+OUTFILE\b)",
        r"(\bLOAD_FILE\b)",
        r"(BENCHMARK\s*\()",
        r"(SLEEP\s*\()",
        r"(0x[0-9a-fA-F]+)",
        r"(CHAR\s*\(\d+\))",
    ]
    
    # Patrones de XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript\s*:",
        r"on\w+\s*=",
        r"<\s*iframe",
        r"<\s*object",
        r"<\s*embed",
        r"<\s*link",
        r"<\s*style",
        r"<\s*meta",
        r"expression\s*\(",
        r"url\s*\(",
        r"@import",
        r"data\s*:",
        r"vbscript\s*:",
    ]
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Verifica si hay patrones de SQL Injection.
        
        Returns:
            True si detecta posible SQL Injection
        """
        if not value:
            return False
        
        value_upper = value.upper()
        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """
        Verifica si hay patrones de XSS.
        
        Returns:
            True si detecta posible XSS
        """
        if not value:
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitiza un string de entrada.
        
        Args:
            value: Valor a sanitizar
            max_length: Longitud máxima permitida
            
        Returns:
            String sanitizado
        """
        if not value:
            return ""
        
        # Normalizar unicode
        value = unicodedata.normalize('NFKC', value)
        
        # Escapar HTML
        value = html.escape(value)
        
        # Remover caracteres de control
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Limitar longitud
        if len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()
    
    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """
        Sanitiza HTML permitiendo solo texto plano.
        
        Args:
            value: HTML a sanitizar
            
        Returns:
            Texto sin HTML
        """
        if not value:
            return ""
        
        # Remover todas las etiquetas HTML
        clean = re.sub(r'<[^>]+>', '', value)
        
        # Decodificar entidades HTML
        clean = html.unescape(clean)
        
        # Re-escapar para prevenir XSS
        clean = html.escape(clean)
        
        return clean.strip()
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitiza un nombre de archivo.
        
        Args:
            filename: Nombre de archivo
            
        Returns:
            Nombre de archivo seguro
        """
        if not filename:
            return ""
        
        # Remover path traversal
        filename = filename.replace('..', '')
        filename = filename.replace('/', '').replace('\\', '')
        
        # Solo permitir caracteres seguros
        safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limitar longitud
        if len(safe_chars) > 255:
            name, ext = safe_chars.rsplit('.', 1) if '.' in safe_chars else (safe_chars, '')
            safe_chars = name[:250] + ('.' + ext if ext else '')
        
        return safe_chars


class InputValidator:
    """Validación de entrada con reglas específicas."""
    
    # Regex patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_.-]{3,50}$'
    PHONE_PATTERN = r'^[\d\s+()-]{7,20}$'
    CUIT_PATTERN = r'^\d{2}-?\d{8}-?\d{1}$'
    DNI_PATTERN = r'^\d{7,8}$'
    PATENTE_PATTERN = r'^[A-Z]{2,3}\d{3}[A-Z]{0,2}$|^[A-Z]{3}\d{3}$'
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato de email.
        
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if not email:
            return False, "Email requerido"
        
        email = email.strip().lower()
        
        if len(email) > 254:
            return False, "Email demasiado largo"
        
        if not re.match(cls.EMAIL_PATTERN, email):
            return False, "Formato de email inválido"
        
        # Verificar dominios sospechosos
        suspicious_domains = ['tempmail', 'throwaway', '10minute', 'guerrilla']
        domain = email.split('@')[1]
        for suspicious in suspicious_domains:
            if suspicious in domain.lower():
                return False, "Dominio de email no permitido"
        
        return True, None
    
    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, Optional[str]]:
        """Valida nombre de usuario."""
        if not username:
            return False, "Usuario requerido"
        
        username = username.strip()
        
        if len(username) < 3:
            return False, "Usuario debe tener al menos 3 caracteres"
        
        if len(username) > 50:
            return False, "Usuario demasiado largo"
        
        if not re.match(cls.USERNAME_PATTERN, username):
            return False, "Usuario solo puede contener letras, números, guiones y puntos"
        
        # Palabras reservadas
        reserved = ['admin', 'root', 'system', 'administrator', 'null', 'undefined']
        if username.lower() in reserved:
            return False, "Nombre de usuario reservado"
        
        return True, None
    
    @classmethod
    def validate_password(
        cls,
        password: str,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False
    ) -> Tuple[bool, Optional[str], int]:
        """
        Valida fortaleza de contraseña.
        
        Returns:
            Tupla (es_válida, mensaje_error, puntuación_fortaleza)
        """
        if not password:
            return False, "Contraseña requerida", 0
        
        strength = 0
        
        # Longitud
        if len(password) < min_length:
            return False, f"Contraseña debe tener al menos {min_length} caracteres", 0
        
        if len(password) >= 8:
            strength += 1
        if len(password) >= 12:
            strength += 1
        if len(password) >= 16:
            strength += 1
        
        # Mayúsculas
        has_upper = bool(re.search(r'[A-Z]', password))
        if require_uppercase and not has_upper:
            return False, "Contraseña debe contener al menos una mayúscula", strength
        if has_upper:
            strength += 1
        
        # Minúsculas
        has_lower = bool(re.search(r'[a-z]', password))
        if require_lowercase and not has_lower:
            return False, "Contraseña debe contener al menos una minúscula", strength
        if has_lower:
            strength += 1
        
        # Dígitos
        has_digit = bool(re.search(r'\d', password))
        if require_digit and not has_digit:
            return False, "Contraseña debe contener al menos un número", strength
        if has_digit:
            strength += 1
        
        # Caracteres especiales
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        if require_special and not has_special:
            return False, "Contraseña debe contener al menos un carácter especial", strength
        if has_special:
            strength += 2
        
        # Verificar patrones comunes
        common_patterns = ['123456', 'password', 'qwerty', 'abc123', 'admin']
        if password.lower() in common_patterns:
            return False, "Contraseña demasiado común", 0
        
        return True, None, min(strength, 10)
    
    @classmethod
    def validate_phone(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """Valida número de teléfono."""
        if not phone:
            return True, None  # Opcional
        
        phone = phone.strip()
        
        # Remover caracteres de formato
        clean_phone = re.sub(r'[\s+()-]', '', phone)
        
        if not clean_phone.isdigit():
            return False, "Teléfono solo puede contener números"
        
        if len(clean_phone) < 7 or len(clean_phone) > 15:
            return False, "Longitud de teléfono inválida"
        
        return True, None
    
    @classmethod
    def validate_cuit(cls, cuit: str) -> Tuple[bool, Optional[str]]:
        """Valida CUIT argentino."""
        if not cuit:
            return True, None  # Opcional
        
        # Limpiar formato
        cuit = re.sub(r'[^0-9]', '', cuit)
        
        if len(cuit) != 11:
            return False, "CUIT debe tener 11 dígitos"
        
        # Validar dígito verificador
        base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(cuit[i]) * base[i] for i in range(10))
        remainder = 11 - (total % 11)
        
        if remainder == 11:
            verificador = 0
        elif remainder == 10:
            verificador = 9
        else:
            verificador = remainder
        
        if int(cuit[10]) != verificador:
            return False, "CUIT inválido"
        
        return True, None
    
    @classmethod
    def validate_patente(cls, patente: str) -> Tuple[bool, Optional[str]]:
        """Valida patente argentina."""
        if not patente:
            return True, None  # Opcional
        
        patente = patente.upper().strip()
        patente = re.sub(r'[\s-]', '', patente)
        
        # Formato viejo: AAA123
        # Formato nuevo: AA123AA
        old_format = r'^[A-Z]{3}\d{3}$'
        new_format = r'^[A-Z]{2}\d{3}[A-Z]{2}$'
        
        if not (re.match(old_format, patente) or re.match(new_format, patente)):
            return False, "Formato de patente inválido"
        
        return True, None
    
    @classmethod
    def validate_and_sanitize(
        cls,
        value: Any,
        field_name: str,
        required: bool = False,
        max_length: int = 1000,
        check_injection: bool = True,
        validator: str = None
    ) -> str:
        """
        Valida y sanitiza un valor de entrada.
        
        Args:
            value: Valor a validar
            field_name: Nombre del campo (para mensajes de error)
            required: Si el campo es requerido
            max_length: Longitud máxima
            check_injection: Si verificar SQL/XSS injection
            validator: Validador específico ('email', 'username', 'phone', etc.)
            
        Returns:
            Valor sanitizado
            
        Raises:
            InvalidInputException: Si la validación falla
            SQLInjectionDetected: Si se detecta SQL injection
            XSSDetected: Si se detecta XSS
        """
        # Convertir a string
        if value is None:
            value = ""
        value = str(value).strip()
        
        # Requerido
        if required and not value:
            raise InvalidInputException(field_name, "Campo requerido")
        
        if not value:
            return ""
        
        # Verificar inyección
        if check_injection:
            if Sanitizer.check_sql_injection(value):
                raise SQLInjectionDetected(field_name)
            if Sanitizer.check_xss(value):
                raise XSSDetected(field_name)
        
        # Validador específico
        if validator:
            validators = {
                'email': cls.validate_email,
                'username': cls.validate_username,
                'phone': cls.validate_phone,
                'cuit': cls.validate_cuit,
                'patente': cls.validate_patente,
            }
            
            if validator in validators:
                is_valid, error = validators[validator](value)
                if not is_valid:
                    raise InvalidInputException(field_name, error)
        
        # Sanitizar
        return Sanitizer.sanitize_string(value, max_length)
