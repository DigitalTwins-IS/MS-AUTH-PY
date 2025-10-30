"""
Schemas de Autenticación
"""
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@digitaltwins.com",
                "password": "admin123"
            }
        }


class UserResponse(BaseModel):
    """Schema para respuesta de usuario"""
    id: int = Field(..., description="ID del usuario")
    name: str = Field(..., description="Nombre del usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    role: str = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Estado activo del usuario")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    temporary_password: Optional[str] = Field(None, description="Contraseña temporal generada (solo en creación)")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Administrador Principal",
                "email": "admin@digitaltwins.com",
                "role": "admin",
                "is_active": True,
                "created_at": "2025-10-02T00:00:00Z"
            }
        }


class Token(BaseModel):
    """Schema para token JWT"""
    access_token: str = Field(..., description="Token de acceso JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user: UserResponse = Field(..., description="Información del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "name": "Administrador",
                    "email": "admin@digitaltwins.com",
                    "role": "admin",
                    "is_active": True
                }
            }
        }


class TokenData(BaseModel):
    """Schema para datos del token"""
    email: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    """Schema para crear usuario"""
    name: str = Field(..., min_length=3, max_length=50, description="Nombre del usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    role: str = Field(..., description="Rol del usuario")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="Contraseña manual (opcional, se genera automáticamente si no se proporciona)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nuevo Usuario",
                "email": "nuevo@digitaltwins.com",
                "role": "admin",
                "password": "MiContraseña123!"
            }
        }


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    name: Optional[str] = Field(None, min_length=3, max_length=50, description="Nombre del usuario")
    email: Optional[EmailStr] = Field(None, description="Email del usuario")
    role: Optional[str] = Field(None, description="Rol del usuario")
    is_active: Optional[bool] = Field(None, description="Estado activo del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Usuario Actualizado",
                "email": "actualizado@digitaltwins.com",
                "role": "cajero",
                "is_active": True
            }
        }


class UserListResponse(BaseModel):
    """Schema para lista de usuarios"""
    id: int = Field(..., description="ID del usuario")
    name: str = Field(..., description="Nombre del usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    role: str = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Estado activo del usuario")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")
    
    class Config:
        from_attributes = True


class PasswordResetResponse(BaseModel):
    """Schema para respuesta de restablecimiento de contraseña"""
    message: str = Field(..., description="Mensaje de confirmación")
    temporary_password: str = Field(..., description="Contraseña temporal generada")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Nueva contraseña generada exitosamente",
                "temporary_password": "TempPass123!"
            }
        }


class RoleInfo(BaseModel):
    """Schema para información de un rol"""
    value: str = Field(..., description="Valor del rol")
    label: str = Field(..., description="Etiqueta del rol")
    description: str = Field(..., description="Descripción del rol")


class RolesResponse(BaseModel):
    """Schema para respuesta de roles disponibles"""
    roles: list[RoleInfo] = Field(..., description="Lista de roles disponibles")


class HealthResponse(BaseModel):
    """Schema para health check"""
    status: str = Field(..., description="Estado del servicio")
    service: str = Field(..., description="Nombre del servicio")
    version: str = Field(..., description="Versión del servicio")
    database: str = Field(..., description="Estado de la base de datos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "MS-AUTH-PY",
                "version": "1.0.0",
                "database": "connected"
            }
        }

