"""
Endpoints de Soporte - Contacto por email
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.core.config import settings

router = APIRouter()

# Email de destino para soporte
SUPPORT_EMAIL = "lateoriadelcrecimiento@gmail.com"


class ContactFormRequest(BaseModel):
    """Esquema para el formulario de contacto"""
    nombre: str
    email: EmailStr
    asunto: str
    mensaje: str


class ContactFormResponse(BaseModel):
    """Respuesta del envío de formulario"""
    success: bool
    message: str


@router.post("/contact", response_model=ContactFormResponse)
async def send_contact_form(data: ContactFormRequest) -> Any:
    """
    Envía un formulario de contacto de soporte por email.
    No requiere autenticación.
    """
    try:
        # Crear el mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Soporte de Gestion de Taller] {data.asunto}"
        msg['From'] = settings.SMTP_USER
        msg['To'] = SUPPORT_EMAIL
        msg['Reply-To'] = data.email

        # Contenido HTML del email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%); color: white; padding: 24px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 24px; }}
                .field {{ margin-bottom: 16px; }}
                .field-label {{ font-weight: bold; color: #374151; font-size: 12px; text-transform: uppercase; margin-bottom: 4px; }}
                .field-value {{ color: #1f2937; padding: 12px; background-color: #f9fafb; border-radius: 8px; border-left: 3px solid #3b82f6; }}
                .message-box {{ background-color: #f0f9ff; padding: 16px; border-radius: 8px; border: 1px solid #bae6fd; }}
                .footer {{ background-color: #f3f4f6; padding: 16px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📧 Nueva Solicitud de Soporte</h1>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="field-label">Nombre</div>
                        <div class="field-value">{data.nombre}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Email de contacto</div>
                        <div class="field-value"><a href="mailto:{data.email}">{data.email}</a></div>
                    </div>
                    <div class="field">
                        <div class="field-label">Asunto</div>
                        <div class="field-value">{data.asunto}</div>
                    </div>
                    <div class="field">
                        <div class="field-label">Mensaje</div>
                        <div class="message-box">{data.mensaje.replace(chr(10), '<br>')}</div>
                    </div>
                </div>
                <div class="footer">
                    Enviado desde Gestión de Taller • {datetime.now().strftime('%d/%m/%Y %H:%M')}
                </div>
            </div>
        </body>
        </html>
        """

        # Contenido de texto plano como alternativa
        text_content = f"""
Nueva Solicitud de Soporte - Gestión de Taller
==============================================

Nombre: {data.nombre}
Email: {data.email}
Asunto: {data.asunto}

Mensaje:
{data.mensaje}

--
Enviado: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """

        # Adjuntar ambas versiones
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Enviar el email
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, SUPPORT_EMAIL, msg.as_string())

        return ContactFormResponse(
            success=True,
            message="Mensaje enviado correctamente"
        )

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Error de autenticación del servidor de correo"
        )
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar el correo: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}"
        )
