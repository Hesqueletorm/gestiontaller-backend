"""
Endpoints de Registro y Verificación de Email
Con seguridad mejorada: rate limiting, validación, auditoría
"""
from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.core.email import send_verification_email
from app.crud.crud_user import user as crud_user
from app.crud.crud_lubricentro import lubricentro as crud_lubricentro
from app.schemas.user import UserCreate
from app.schemas.verification import (
    RegisterRequest, 
    VerifyEmailRequest, 
    ResendCodeRequest, 
    RegisterResponse
)
from app.schemas.lubricentro import LubricentroSimple, LubricentroListResponse
from .utils import (
    codigos_pendientes,
    generar_codigo,
    limpiar_codigos_expirados
)

# Importar módulo de seguridad
from app.core.security.rate_limiter import registration_limiter
from app.core.security.audit_logger import audit_logger, SecurityEventType
from app.core.security.validators import InputValidator, Sanitizer
from app.core.security.exceptions import RateLimitExceeded, InvalidInputException
from app.core.security.middleware import get_client_ip

router = APIRouter()


@router.get("/lubricentros/publicos", response_model=LubricentroListResponse)
def listar_lubricentros_publicos(
    db: Session = Depends(deps.get_db)
):
    """
    Listar lubricentros activos disponibles para unirse.
    Endpoint público (no requiere autenticación).
    """
    lubricentros = crud_lubricentro.get_all_active(db)
    return LubricentroListResponse(lubricentros=lubricentros)


@router.post("/register", response_model=RegisterResponse)
def register_user(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Iniciar registro de usuario. Envía código de verificación por email.
    
    Sistema de Roles:
    - DESARROLLADOR (0): Solo usuario 'admin', asignado manualmente
    - ADMINISTRADOR (1): Se asigna al crear un nuevo lubricentro
    - COORDINADOR (2): Asignado por el Administrador
    - OPERADOR (3): Por defecto al unirse a un lubricentro existente
    
    Seguridad:
    - Rate limiting por IP
    - Validación y sanitización de entrada
    - Auditoría de intentos de registro
    """
    # Obtener IP del cliente
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")
    
    # Verificar rate limiting por IP
    if not registration_limiter.is_allowed(client_ip):
        retry_after = registration_limiter.get_retry_after(client_ip)
        audit_logger.log_rate_limit_exceeded(
            identifier=client_ip,
            limiter_name="registration",
            ip_address=client_ip
        )
        raise RateLimitExceeded(retry_after=retry_after)
    
    # Limpiar códigos expirados
    limpiar_codigos_expirados()
    
    # Sanitizar y validar entrada
    try:
        # Sanitizar campos de texto
        usuario_sanitizado = Sanitizer.sanitize_string(request.usuario)
        email_sanitizado = request.email.lower().strip()
        nombre_sanitizado = Sanitizer.sanitize_string(request.nombre) if request.nombre else None
        
        # Validar formato de email
        is_valid_email, email_error = InputValidator.validate_email(email_sanitizado)
        if not is_valid_email:
            raise InvalidInputException(field="email", reason=email_error or "Formato de email inválido")
        
        # Validar usuario
        is_valid, error_msg = InputValidator.validate_username(usuario_sanitizado)
        if not is_valid:
            raise InvalidInputException(field="usuario", reason=error_msg)
        
        # Validar fortaleza de contraseña
        is_strong, password_error, _ = InputValidator.validate_password(
            request.password,
            min_length=6,
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=False
        )
        if not is_strong:
            raise InvalidInputException(
                field="password", 
                reason=password_error or "Contraseña inválida"
            )
            
    except InvalidInputException as e:
        audit_logger.log(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            success=False,
            username=request.usuario,
            ip_address=client_ip,
            message="Validación de registro fallida",
            details={
                "field": e.field,
                "reason": e.reason,
                "email": request.email
            }
        )
        raise
    
    # Validar longitud de usuario
    if len(usuario_sanitizado) < 3:
        raise HTTPException(
            status_code=400, 
            detail="El usuario debe tener al menos 3 caracteres"
        )
    
    # Validar longitud de contraseña
    if len(request.password) < 6:
        raise HTTPException(
            status_code=400, 
            detail="La contraseña debe tener al menos 6 caracteres"
        )
    
    # Validar datos del lubricentro según la opción elegida
    lubricentro_id = None
    rol = 3  # Por defecto Operador
    
    if request.crear_lubricentro:
        # Crear nuevo lubricentro - necesita nombre
        if not request.nombre_lubricentro or len(request.nombre_lubricentro.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Debes proporcionar un nombre para tu lubricentro (mínimo 3 caracteres)"
            )
        rol = 1  # Administrador del nuevo lubricentro
    else:
        # Unirse a lubricentro existente - necesita código
        if not request.codigo_lubricentro:
            raise HTTPException(
                status_code=400,
                detail="Debes seleccionar un lubricentro para unirte"
            )
        # Verificar que el lubricentro existe
        lubricentro = crud_lubricentro.obtener_por_codigo(db, codigo=request.codigo_lubricentro)
        if not lubricentro:
            raise HTTPException(
                status_code=400,
                detail="El lubricentro seleccionado no existe"
            )
        if not lubricentro.activo:
            raise HTTPException(
                status_code=400,
                detail="El lubricentro seleccionado no está activo"
            )
        lubricentro_id = lubricentro.id
        
        # Verificar que el usuario no existe en ese lubricentro
        existing_in_lubri = crud_user.get_by_username_and_lubricentro(
            db, username=request.usuario, lubricentro_id=lubricentro_id
        )
        if existing_in_lubri:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un usuario '{request.usuario}' en este lubricentro"
            )
    
    # Verificar si el email ya existe (global)
    existing_email = crud_user.get_by_email(db, email=request.email)
    if existing_email:
        raise HTTPException(
            status_code=400, 
            detail="El email ya está registrado"
        )
    
    # Generar código de verificación
    codigo = generar_codigo()
    
    # Los usuarios que crean nuevos talleres necesitan aprobación por el administrador de Maldonado Master
    # Los usuarios que se unen a lubricentros existentes también necesitan aprobación del admin del lubricentro
    # En ambos casos, aprobado = False hasta que sea aprobado manualmente
    necesita_aprobacion = True  # Todos los usuarios nuevos necesitan aprobación
    
    # Guardar datos temporalmente ANTES de enviar email
    codigos_pendientes[email_sanitizado] = {
        'codigo': codigo,
        'timestamp': datetime.now(),
        'usuario': usuario_sanitizado,
        'password': request.password,
        'nombre': nombre_sanitizado,
        'crear_lubricentro': request.crear_lubricentro,
        'nombre_lubricentro': request.nombre_lubricentro,
        'lubricentro_id': lubricentro_id,
        'rol': rol,
        'aprobado': not necesita_aprobacion  # False si necesita aprobación
    }
    
    # Registrar intento de rate limiter
    registration_limiter.record_attempt(client_ip, success=True)
    
    # Auditar intento de registro
    audit_logger.log(
        event_type=SecurityEventType.ACCOUNT_CREATED,
        success=True,
        username=usuario_sanitizado,
        ip_address=client_ip,
        message="Código de verificación enviado",
        details={
            "email": email_sanitizado,
            "lubricentro_id": lubricentro_id,
            "crear_lubricentro": request.crear_lubricentro
        }
    )
    
    # Enviar email de forma inmediata para evitar demoras
    try:
        success, msg = send_verification_email(email_sanitizado, codigo, usuario_sanitizado)
        if not success:
            print(f"[REGISTER] Error enviando email: {msg}")
            # Aún así guardamos el código por si quiere reenviar
    except Exception as e:
        print(f"[REGISTER] Excepción enviando email: {e}")
    
    return RegisterResponse(
        success=True,
        message=f"Código enviado a {email_sanitizado}",
        email=email_sanitizado
    )


@router.post("/verify-email", response_model=RegisterResponse)
def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Verificar código de email y crear usuario.
    Si crear_lubricentro=True, también crea el lubricentro.
    """
    # Limpiar códigos expirados
    limpiar_codigos_expirados()
    
    # Verificar si hay código pendiente para este email
    if request.email not in codigos_pendientes:
        raise HTTPException(
            status_code=400, 
            detail="No hay código pendiente para este email. Iniciá el registro nuevamente."
        )
    
    datos = codigos_pendientes[request.email]
    
    # Verificar si el código ha expirado
    if (datetime.now() - datos['timestamp']) > timedelta(minutes=10):
        del codigos_pendientes[request.email]
        raise HTTPException(
            status_code=400, 
            detail="El código ha expirado. Solicitá uno nuevo."
        )
    
    # Verificar código
    if datos['codigo'] != request.codigo:
        raise HTTPException(
            status_code=400, 
            detail="Código incorrecto"
        )
    
    # Crear lubricentro si es necesario
    try:
        lubricentro_id = datos.get('lubricentro_id')
        
        if datos.get('crear_lubricentro'):
            # Crear nuevo lubricentro
            nuevo_lubricentro = crud_lubricentro.crear(
                db,
                nombre=datos['nombre_lubricentro']
            )
            lubricentro_id = nuevo_lubricentro.id
            print(f"[REGISTER] Lubricentro creado: {nuevo_lubricentro.nombre} (ID: {lubricentro_id}, Código: {nuevo_lubricentro.codigo})")
        
        # Crear usuario
        user_create = UserCreate(
            usuario=datos['usuario'],
            email=request.email,
            password=datos['password'],
            nombre=datos.get('nombre'),
            lubricentro_id=lubricentro_id,
            rol=datos.get('rol', 0),
            aprobado=datos.get('aprobado', True)  # False si necesita aprobación
        )
        nuevo_usuario = crud_user.create(db, obj_in=user_create)
        
        # Limpiar código usado
        del codigos_pendientes[request.email]
        
        # Mapear rol a texto
        rol_map = {0: "Desarrollador", 1: "Administrador", 2: "Coordinador", 3: "Operador"}
        rol_texto = rol_map.get(datos.get('rol', 3), "Operador")
        
        # Mensaje según si necesita aprobación o no
        if datos.get('aprobado', True):
            mensaje_final = f"¡Cuenta creada exitosamente como {rol_texto}! Ya podés iniciar sesión."
        else:
            mensaje_final = f"¡Cuenta creada! Tu solicitud fue enviada al administrador del lubricentro. Recibirás acceso cuando sea aprobada."
        
        return RegisterResponse(
            success=True,
            message=mensaje_final,
            email=request.email
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al crear usuario: {str(e)}"
        )


@router.post("/resend-code", response_model=RegisterResponse)
def resend_code(
    request: ResendCodeRequest,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Reenviar código de verificación.
    """
    # Verificar si hay datos pendientes para este email
    if request.email not in codigos_pendientes:
        raise HTTPException(
            status_code=400, 
            detail="No hay registro pendiente para este email. Iniciá el registro nuevamente."
        )
    
    datos = codigos_pendientes[request.email]
    
    # Generar nuevo código
    nuevo_codigo = generar_codigo()
    
    # Actualizar código y timestamp ANTES de enviar
    codigos_pendientes[request.email]['codigo'] = nuevo_codigo
    codigos_pendientes[request.email]['timestamp'] = datetime.now()
    
    # Enviar email de forma inmediata
    try:
        success, msg = send_verification_email(request.email, nuevo_codigo, datos['usuario'])
        if not success:
            print(f"[RESEND] Error enviando email: {msg}")
    except Exception as e:
        print(f"[RESEND] Excepción enviando email: {e}")
    
    return RegisterResponse(
        success=True,
        message="Código reenviado exitosamente",
        email=request.email
    )
