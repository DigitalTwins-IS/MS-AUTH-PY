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
    name: str = Field(..., min_length=3, max_length=255, description="Nombre del usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")
    role: str = Field(default="admin", description="Rol del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nuevo Usuario",
                "email": "nuevo@digitaltwins.com",
                "password": "password123",
                "role": "admin"
            }
        }


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

