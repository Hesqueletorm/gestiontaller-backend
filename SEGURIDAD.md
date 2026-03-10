# 🔒 Sistema de Seguridad - Gestión de Taller

## Resumen

Este documento describe el sistema de seguridad implementado para proteger la aplicación Gestión de Taller contra ataques comunes y cumplir con las mejores prácticas de seguridad.

## Módulos Implementados

### 1. Rate Limiting (`app/core/security/rate_limiter.py`)

Protección contra ataques de fuerza bruta mediante limitación de solicitudes.

#### Limitadores Disponibles:

| Limitador | Solicitudes | Ventana | Bloqueo | Uso |
|-----------|-------------|---------|---------|-----|
| `login_limiter` | 5 | 5 min | 15 min | Endpoint de login |
| `ip_limiter` | 100 | 1 min | 5 min | Global por IP |
| `api_limiter` | 60 | 1 min | 2 min | APIs autenticadas |
| `password_reset_limiter` | 3 | 60 min | 30 min | Recuperación de contraseña |
| `registration_limiter` | 5 | 60 min | 30 min | Registro de usuarios |

#### Uso en Código:

```python
from app.core.security.rate_limiter import login_limiter

# Verificar si permitido
if not login_limiter.is_allowed(identifier):
    raise RateLimitExceeded(retry_after=login_limiter.get_retry_after(identifier))

# Registrar intento
login_limiter.record_attempt(identifier, success=False)
```

### 2. Auditoría de Seguridad (`app/core/security/audit_logger.py`)

Sistema de logging estructurado en JSON para eventos de seguridad.

#### Eventos Registrados:

- **Autenticación**: Login exitoso/fallido, logout
- **Gestión de Cuentas**: Registro, bloqueo, cambio de contraseña
- **Seguridad**: Rate limiting, acceso no autorizado, detección de ataques
- **Administración**: Cambios de permisos, activación/desactivación de usuarios

#### Ubicación de Logs:

```
backend/logs/security_audit.log
```

#### Formato de Log:

```json
{
  "timestamp": "2025-01-15T10:30:00.123456",
  "event_type": "LOGIN_SUCCESS",
  "severity": "INFO",
  "user_id": 123,
  "username": "usuario1",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {}
}
```

### 3. Validación de Entrada (`app/core/security/validators.py`)

Prevención de SQL Injection y XSS mediante sanitización y validación.

#### Funcionalidades:

- **Sanitizer**: Limpia strings de caracteres peligrosos
  - `sanitize_string()`: Elimina patrones SQL/XSS
  - `sanitize_html()`: Escapa tags HTML
  - `sanitize_filename()`: Limpia nombres de archivo

- **InputValidator**: Valida formatos de datos
  - `validate_email()`: Formato de email
  - `validate_username()`: Formato de usuario
  - `validate_password_strength()`: Fortaleza de contraseña
  - `validate_cuit()`: CUIT argentino
  - `validate_patente_argentina()`: Patentes de vehículos

### 4. Middleware de Seguridad (`app/core/security/middleware.py`)

Headers de seguridad y rate limiting global.

#### Headers Agregados:

| Header | Valor | Protección |
|--------|-------|------------|
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | XSS reflejado |
| `Strict-Transport-Security` | `max-age=31536000` | Forzar HTTPS |
| `Content-Security-Policy` | `default-src 'self'...` | Inyección de contenido |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Fuga de referrer |
| `Permissions-Policy` | Restrictivo | APIs del navegador |

### 5. Excepciones Personalizadas (`app/core/security/exceptions.py`)

Respuestas HTTP consistentes para eventos de seguridad.

```python
RateLimitExceeded(retry_after=60)    # HTTP 429
AccountLockedException(minutes_remaining=15)  # HTTP 423
InvalidInputException(field="email", reason="formato inválido")  # HTTP 400
SQLInjectionDetected(input_value="...")  # HTTP 403
XSSDetected(input_value="...")  # HTTP 403
```

## Configuración

### Variables de Entorno (`.env`)

```env
# Rate Limiting
LOGIN_RATE_LIMIT_MAX_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=300
LOGIN_RATE_LIMIT_BLOCK_SECONDS=900

# Auditoría
AUDIT_LOG_ENABLED=true
AUDIT_LOG_PATH=logs/security_audit.log

# Headers
SECURITY_HEADERS_ENABLED=true
```

### Configuración en `config.py`

Todas las configuraciones tienen valores por defecto seguros y pueden ser sobreescritas mediante variables de entorno.

## Endpoints Protegidos

### Login (`/api/v1/login/access-token`)

- ✅ Rate limiting por usuario+IP
- ✅ Bloqueo tras 5 intentos fallidos
- ✅ Auditoría de todos los intentos
- ✅ Mensajes de error genéricos

### Registro (`/api/v1/login/register`)

- ✅ Rate limiting por IP
- ✅ Sanitización de entrada
- ✅ Validación de email/usuario/contraseña
- ✅ Auditoría de registros

### Recuperación de Contraseña (`/api/v1/login/recuperar-password`)

- ✅ Rate limiting estricto (3/hora)
- ✅ No revela si el email existe
- ✅ Auditoría completa

## Monitoreo

### Endpoint de Salud

```
GET /api/v1/health
```

Respuesta:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00",
  "version": "1.0.0"
}
```

### Estado de Seguridad (Admin)

```
GET /api/v1/security-status
Authorization: Bearer <token_admin>
```

Muestra configuración activa y estadísticas de rate limiting.

## Buenas Prácticas

### Para Desarrolladores

1. **Siempre usar los validadores** antes de procesar input del usuario
2. **Registrar eventos de seguridad** usando `audit_logger`
3. **No revelar información sensible** en mensajes de error
4. **Usar las excepciones personalizadas** para respuestas consistentes

### Para DevOps

1. **Rotar logs regularmente** (configurado automáticamente)
2. **Monitorear archivos de log** para detectar patrones sospechosos
3. **Revisar IPs bloqueadas** periódicamente
4. **Mantener SECRET_KEY segura** y rotarla periódicamente

## Roadmap Futuro

- [ ] Autenticación de dos factores (2FA/TOTP)
- [ ] Detección de anomalías con ML
- [ ] Integración con SIEM
- [ ] Rate limiting distribuido con Redis
- [ ] Web Application Firewall (WAF)

## Contacto

Para reportar vulnerabilidades de seguridad, contactar al equipo de desarrollo.
