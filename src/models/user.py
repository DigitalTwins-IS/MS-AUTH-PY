from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from .database import Base
import enum


class UserRole(str, enum.Enum):
    """Roles de usuario disponibles"""
    ADMIN = "ADMIN"
    TENDERO = "TENDERO"
    VENDEDOR = "VENDEDOR"


class User(Base):
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ADMIN, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    # Campos para seguridad adicional
    phone_number = Column(String(20), nullable=True, index=True)  # Teléfono para SMS
    security_question = Column(String(255), nullable=True)  # Pregunta de seguridad
    security_answer_hash = Column(String(255), nullable=True)  # Respuesta hasheada
    # Campos para restablecimiento de contraseña
    reset_token = Column(String(255), nullable=True, index=True)
    reset_code = Column(String(6), nullable=True, index=True)  # Código de 6 dígitos para SMS
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    reset_code_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, active={self.is_active})>"

