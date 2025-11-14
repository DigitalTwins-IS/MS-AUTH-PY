"""
Utilidades de seguridad para manejo de contraseñas
"""
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Contexto para bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña
        
    Returns:
        bool: True si coinciden, False si no
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera un hash bcrypt de una contraseña
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        str: Hash de la contraseña
    """
    return pwd_context.hash(password)


def generate_reset_token() -> str:
    """
    Returns:
        str: Token aleatorio seguro de 32 bytes en formato URL-safe
    """
    return secrets.token_urlsafe(32)


def get_reset_token_expiration(hours: int = 1) -> datetime:
    """
    Calcula la fecha de expiración para un token de reset
    
    Args:
        hours: Horas de validez del token (por defecto 1 hora)
        
    Returns:
        datetime: Fecha y hora de expiración (timezone-aware)
    """
    from datetime import timezone
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def is_reset_token_valid(token_expires: datetime) -> bool:
    """
    Verifica si un token de reset aún es válido (no ha expirado)
    
    Args:
        token_expires: Fecha de expiración del token (puede ser timezone-aware o naive)
        
    Returns:
        bool: True si el token es válido, False si ha expirado
    """
    if token_expires is None:
        return False
    
    from datetime import timezone
    
    # Normalizar a timezone-aware si es necesario
    now = datetime.now(timezone.utc)
    
    # Si token_expires es naive, asumir UTC
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)
    
    return now < token_expires


def generate_reset_code() -> str:
    """
    
    Returns:
        str: Código de 6 dígitos (ej: "123456")
    """
    return f"{secrets.randbelow(1000000):06d}"


def get_reset_code_expiration(minutes: int = 10) -> datetime:
    """
    Calcula la fecha de expiración para un código de reset (más corto que token)
    
    Args:
        minutes: Minutos de validez del código (por defecto 10 minutos)
        
    Returns:
        datetime: Fecha y hora de expiración (timezone-aware)
    """
    from datetime import timezone
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def is_reset_code_valid(code_expires: datetime) -> bool:
    """
    Verifica si un código de reset aún es válido (no ha expirado)
    
    Args:
        code_expires: Fecha de expiración del código (puede ser timezone-aware o naive)
        
    Returns:
        bool: True si el código es válido, False si ha expirado
    """
    if code_expires is None:
        return False
    
    from datetime import timezone
    
    # Normalizar a timezone-aware si es necesario
    now = datetime.now(timezone.utc)
    
    # Si code_expires es naive, asumir UTC
    if code_expires.tzinfo is None:
        code_expires = code_expires.replace(tzinfo=timezone.utc)
    
    return now < code_expires


def hash_security_answer(answer: str) -> str:
    """
    Genera un hash de la respuesta de seguridad (similar a contraseña)
    
    Args:
        answer: Respuesta de seguridad en texto plano
        
    Returns:
        str: Hash de la respuesta
    """
    return pwd_context.hash(answer.lower().strip())


def verify_security_answer(plain_answer: str, hashed_answer: str) -> bool:
    """
    Verifica si una respuesta de seguridad coincide con su hash
    
    Args:
        plain_answer: Respuesta en texto plano
        hashed_answer: Hash de la respuesta
        
    Returns:
        bool: True si coinciden, False si no
    """
    return pwd_context.verify(plain_answer.lower().strip(), hashed_answer)

