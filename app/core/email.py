# Servicio de Email para verificación de usuarios
# Usa SMTP de Gmail para enviar códigos de verificación

import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

from app.core.config import settings


def send_verification_email(destinatario: str, codigo: str, usuario: str) -> Tuple[bool, str]:
    """
    Envía un email con el código de verificación al usuario.
    
    Args:
        destinatario: Email del usuario
        codigo: Código de 6 dígitos
        usuario: Nombre de usuario
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    if not destinatario:
        return False, "Destinatario vacío"
    
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT
    sender_email = settings.SMTP_USER
    sender_password = settings.SMTP_PASSWORD
    
    if not sender_email or not sender_password:
        return False, "Configuración de email incompleta (remitente/contraseña)"
    
    # Limpiar espacios de la contraseña (Gmail App Password viene con espacios)
    sender_password = re.sub(r"\s+", "", sender_password)
    
    # Crear mensaje
    msg = MIMEMultipart()
    msg["From"] = f"Maldonexus.inc <{sender_email}>"
    msg["To"] = destinatario
    msg["Subject"] = f"Maldonexus.inc - Código de verificación: {codigo}"
    
    cuerpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .header h1 {{ color: #FFA000; margin: 0; }}
            .code {{ font-size: 32px; font-weight: bold; text-align: center; background: linear-gradient(135deg, #FFA000, #f8ed19); color: white; padding: 15px; border-radius: 8px; letter-spacing: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛢️ Sistema de Gestión</h1>
            </div>
            <p>Hola <strong>{usuario}</strong>,</p>
            <p>Tu código de verificación es:</p>
            <div class="code">{codigo}</div>
            <p>Este código es válido por <strong>10 minutos</strong>.</p>
            <p>Si no solicitaste este código, podés ignorar este mensaje.</p>
            <div class="footer">
                <p>Maldonexus.inc - Sistema de Gestión</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))
    
    try:
        # Usar STARTTLS para puerto 587
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [destinatario], msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.ehlo()
                try:
                    server.starttls()
                    server.ehlo()
                except smtplib.SMTPException:
                    pass
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [destinatario], msg.as_string())
        return True, "Email enviado correctamente"
    except smtplib.SMTPAuthenticationError as e:
        if getattr(e, "smtp_code", None) == 535 or "535" in str(e):
            return False, "Error de autenticación: verificá las credenciales SMTP"
        return False, f"Error de autenticación SMTP: {e}"
    except Exception as e:
        return False, f"Error enviando email: {e}"


def send_recovery_email(destinatario: str, codigo: str) -> Tuple[bool, str]:
    """
    Envía un email con el código de recuperación de contraseña.
    
    Args:
        destinatario: Email del usuario
        codigo: Código de 6 dígitos
        
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    if not destinatario:
        return False, "Destinatario vacío"
    
    smtp_server = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT
    sender_email = settings.SMTP_USER
    sender_password = settings.SMTP_PASSWORD
    
    if not sender_email or not sender_password:
        return False, "Configuración de email incompleta (remitente/contraseña)"
    
    # Limpiar espacios de la contraseña (Gmail App Password viene con espacios)
    sender_password = re.sub(r"\s+", "", sender_password)
    
    # Crear mensaje
    msg = MIMEMultipart()
    msg["From"] = f"Maldonexus.inc <{sender_email}>"
    msg["To"] = destinatario
    msg["Subject"] = f"Maldonexus.inc - Recuperar contraseña - Código: {codigo}"
    
    cuerpo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .header h1 {{ color: #FFA000; margin: 0; }}
            .code {{ font-size: 32px; font-weight: bold; text-align: center; background: linear-gradient(135deg, #FFA000, #f8ed19); color: white; padding: 15px; border-radius: 8px; letter-spacing: 5px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin: 20px 0; color: #856404; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 Recuperar Contraseña</h1>
            </div>
            <p>Recibimos una solicitud para recuperar tu contraseña.</p>
            <p>Tu código de verificación es:</p>
            <div class="code">{codigo}</div>
            <p>Este código es válido por <strong>10 minutos</strong>.</p>
            <div class="warning">
                <strong>⚠️ Importante:</strong> Si no solicitaste recuperar tu contraseña, ignorá este mensaje. Tu cuenta sigue segura.
            </div>
            <div class="footer">
                <p>Maldonexus.inc - Sistema de Gestión</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))
    
    try:
        # Usar STARTTLS para puerto 587
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [destinatario], msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.ehlo()
                try:
                    server.starttls()
                    server.ehlo()
                except smtplib.SMTPException:
                    pass
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, [destinatario], msg.as_string())
        return True, "Email enviado correctamente"
    except smtplib.SMTPAuthenticationError as e:
        if getattr(e, "smtp_code", None) == 535 or "535" in str(e):
            return False, "Error de autenticación: verificá las credenciales SMTP"
        return False, f"Error de autenticación SMTP: {e}"
    except Exception as e:
        return False, f"Error enviando email: {e}"
