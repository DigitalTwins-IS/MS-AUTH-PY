"""
Utilidades para envío de emails
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from ..config import settings


async def send_reset_password_email(
    to_email: str,
    reset_code: Optional[str] = None,
    reset_token: Optional[str] = None,
    user_name: Optional[str] = None
) -> bool:
    """
    Envía email de restablecimiento de contraseña
    
    Args:
        to_email: Email del destinatario
        reset_code: Código de 6 dígitos (si se usa SMS/email)
        reset_token: Token de restablecimiento (si se usa método simple)
        user_name: Nombre del usuario (opcional)
        
    Returns:
        bool: True si se envió correctamente, False si no
    """
    # Si SMTP no está habilitado, no enviar (solo desarrollo)
    if not settings.SMTP_ENABLED:
        print("⚠️ SMTP_ENABLED=False - Email no se enviará, se mostrará en pantalla")
        return False
    
    # Validar configuración SMTP
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"⚠️ Configuración SMTP incompleta - USER: {bool(settings.SMTP_USER)}, PASSWORD: {bool(settings.SMTP_PASSWORD)}")
        return False
    
    print(f"📧 Intentando enviar email a {to_email} desde {settings.SMTP_USER}")
    
    try:
        # Crear mensaje
        message = MIMEMultipart("alternative")
        message["Subject"] = "Restablecimiento de Contraseña - Sistema Digital Twins"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Crear contenido del email
        if reset_code:
            # Email con código de 6 dígitos
            text_content = f"""
Hola {user_name or 'Usuario'},

Has solicitado restablecer tu contraseña en el Sistema Digital Twins.

Tu código de verificación es: {reset_code}

Este código es válido por 10 minutos.

Si no solicitaste este restablecimiento, por favor ignora este email.

Saludos,
Equipo Digital Twins
            """
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .code {{ background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0; border-radius: 5px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Restablecimiento de Contraseña</h2>
        <p>Hola {user_name or 'Usuario'},</p>
        <p>Has solicitado restablecer tu contraseña en el Sistema Digital Twins.</p>
        <div class="code">{reset_code}</div>
        <p>Este código es válido por <strong>10 minutos</strong>.</p>
        <p>Si no solicitaste este restablecimiento, por favor ignora este email.</p>
        <div class="footer">
            <p>Saludos,<br>Equipo Digital Twins</p>
        </div>
    </div>
</body>
</html>
            """
        else:
            # Email con token
            reset_url = f"http://localhost:8080/forgot-password?token={reset_token}"
            
            text_content = f"""
Hola {user_name or 'Usuario'},

Has solicitado restablecer tu contraseña en el Sistema Digital Twins.

Tu token de restablecimiento es:
{reset_token}

O haz clic en el siguiente enlace:
{reset_url}

Este token es válido por 1 hora.

Si no solicitaste este restablecimiento, por favor ignora este email.

Saludos,
Equipo Digital Twins
            """
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .token {{ background-color: #f4f4f4; padding: 15px; word-break: break-all; margin: 20px 0; border-radius: 5px; font-family: monospace; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Restablecimiento de Contraseña</h2>
        <p>Hola {user_name or 'Usuario'},</p>
        <p>Has solicitado restablecer tu contraseña en el Sistema Digital Twins.</p>
        <div class="token">{reset_token}</div>
        <p>O haz clic en el siguiente botón:</p>
        <a href="{reset_url}" class="button">Restablecer Contraseña</a>
        <p>Este token es válido por <strong>1 hora</strong>.</p>
        <p>Si no solicitaste este restablecimiento, por favor ignora este email.</p>
        <div class="footer">
            <p>Saludos,<br>Equipo Digital Twins</p>
        </div>
    </div>
</body>
</html>
            """
        
        # Agregar partes al mensaje
        text_part = MIMEText(text_content, "plain", "utf-8")
        html_part = MIMEText(html_content, "html", "utf-8")
        message.attach(text_part)
        message.attach(html_part)
        
        # Enviar email
        print(f"🔐 Conectando a SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        print(f"👤 Usuario SMTP: {settings.SMTP_USER}")
        
        # Gmail usa puerto 587 con STARTTLS (no use_tls)
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD.strip(),  # Quitar espacios si los hay
            start_tls=True if settings.SMTP_PORT == 587 else False,  # STARTTLS para puerto 587
            use_tls=True if settings.SMTP_PORT == 465 else False,  # TLS directo para puerto 465
        )
        
        print(f"✅ Email enviado exitosamente a {to_email}")
        return True
        
    except aiosmtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación SMTP: {str(e)}")
        print(f"   Verifica que la contraseña de aplicación sea correcta")
        print(f"   Usuario: {settings.SMTP_USER}")
        return False
    except aiosmtplib.SMTPException as e:
        print(f"❌ Error SMTP: {str(e)}")
        print(f"   Detalles: HOST={settings.SMTP_HOST}, PORT={settings.SMTP_PORT}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado enviando email: {str(e)}")
        print(f"   Tipo: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

