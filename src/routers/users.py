"""
Router de Gestión de Usuarios
Endpoints: /users (CRUD completo)
"""
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models import get_db, User, UserRole
from ..schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, 
    PasswordResetResponse, RolesResponse, HealthResponse
)
from ..utils import get_current_user, get_password_hash, verify_password
from ..config import settings

router = APIRouter()


def generate_temporary_password() -> str:
    """
    Genera una contraseña temporal que cumple con estándares ISO 27001
    - Mínimo 8 caracteres
    - Al menos 1 mayúscula
    - Al menos 1 minúscula  
    - Al menos 1 número
    - Al menos 1 carácter especial
    """
    length = 12
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    
    # Asegurar al menos un carácter de cada tipo
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Completar con caracteres aleatorios
    all_chars = uppercase + lowercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Mezclar la contraseña
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


@router.get(
    "/users/roles",
    response_model=RolesResponse,
    summary="Obtener roles disponibles",
    description="Obtiene la lista de roles disponibles en el sistema",
    tags=["Gestión de Usuarios"]
)
async def get_available_roles():
    """
    Obtiene la lista de roles disponibles
    
    Returns:
        RolesResponse: Lista de roles con sus descripciones
    """
    from ..schemas import RoleInfo
    
    return RolesResponse(
        roles=[
            RoleInfo(value="ADMIN", label="Administrador", description="Acceso completo al sistema"),
            RoleInfo(value="TENDERO", label="Tendero", description="Gestión de tiendas y establecimientos"),
            RoleInfo(value="VENDEDOR", label="Vendedor", description="Gestión de ventas y clientes")
        ]
    )


@router.get(
    "/users",
    response_model=List[UserListResponse],
    summary="Listar usuarios",
    description="Obtiene la lista de todos los usuarios del sistema",
    tags=["Gestión de Usuarios"]
)
async def list_users(
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos los usuarios del sistema con filtros opcionales
    
    Args:
        is_active: Filtrar por estado activo/inactivo
        role: Filtrar por rol específico
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a retornar
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        List[UserListResponse]: Lista de usuarios
    """
    query = db.query(User)
    
    # Aplicar filtros
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if role:
        query = query.filter(User.role == role)
    
    # Aplicar paginación
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.post(
    "/users",
    response_model=UserResponse,
    summary="Crear usuario",
    description="Crea un nuevo usuario en el sistema con contraseña temporal",
    tags=["Gestión de Usuarios"],
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuevo usuario en el sistema
    
    Args:
        user_data: Datos del nuevo usuario
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        UserResponse: Usuario creado
        
    Raises:
        HTTPException: Si el email ya existe o datos inválidos
    """
    # Validar rol
    valid_roles = [role.value for role in UserRole]
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Roles válidos: {', '.join(valid_roles)}"
        )
    
    # Verificar que el email no exista
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado en el sistema"
        )
    
    # Debug: Imprimir datos recibidos
    print(f"[DEBUG] Datos recibidos: {user_data.model_dump()}")
    print(f"[DEBUG] Contraseña proporcionada: {'SÍ' if user_data.password else 'NO'}")
    
    # Usar contraseña manual si se proporciona, o generar una automática
    if user_data.password:
        print(f"[DEBUG] Usando contraseña manual: {user_data.password[:3]}...")
        # Validar seguridad de contraseña manual (ISO 27001)
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 8 caracteres"
            )
        if not any(c.isupper() for c in user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe contener al menos una mayúscula"
            )
        if not any(c.islower() for c in user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe contener al menos una minúscula"
            )
        if not any(c.isdigit() for c in user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe contener al menos un número"
            )
        user_password = user_data.password
    else:
        # Generar contraseña temporal automática
        user_password = generate_temporary_password()
        print(f"[AUDIT] {datetime.now()}: Se generó contraseña automática para {user_data.email}")
    
    # Crear nuevo usuario
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_password),
        role=UserRole(user_data.role),
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log de auditoría (en producción usar un sistema de logging)
    print(f"[AUDIT] {datetime.now()}: Usuario {current_user.email} creó usuario {new_user.email} con rol {new_user.role}")
    
    # Preparar respuesta
    user_response = UserResponse.model_validate(new_user)
    
    # Si se generó contraseña automática, incluirla en la respuesta
    if not user_data.password:
        user_response.temporary_password = user_password
    
    return user_response


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario",
    description="Obtiene la información de un usuario específico",
    tags=["Gestión de Usuarios"]
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la información de un usuario específico
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        UserResponse: Información del usuario
        
    Raises:
        HTTPException: Si el usuario no existe
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Actualiza la información de un usuario existente",
    tags=["Gestión de Usuarios"]
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la información de un usuario
    
    Args:
        user_id: ID del usuario a actualizar
        user_data: Datos a actualizar
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        UserResponse: Usuario actualizado
        
    Raises:
        HTTPException: Si el usuario no existe o email duplicado
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Validar rol si se proporciona
    if user_data.role:
        valid_roles = [role.value for role in UserRole]
        if user_data.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol inválido. Roles válidos: {', '.join(valid_roles)}"
            )
    
    # Verificar email único si se cambia
    if user_data.email and user_data.email != user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario"
            )
    
    # Actualizar campos
    for field, value in user_data.model_dump(exclude_unset=True).items():
        if field == "role" and value:
            setattr(user, field, UserRole(value))
        else:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Log de auditoría
    print(f"[AUDIT] {datetime.now()}: Usuario {current_user.email} actualizó usuario {user.email}")
    
    return UserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}/toggle-status",
    response_model=UserResponse,
    summary="Activar/Desactivar usuario",
    description="Cambia el estado activo/inactivo de un usuario",
    tags=["Gestión de Usuarios"]
)
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cambia el estado activo/inactivo de un usuario
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        UserResponse: Usuario con estado actualizado
        
    Raises:
        HTTPException: Si el usuario no existe
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Cambiar estado
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    # Log de auditoría
    action = "activó" if user.is_active else "desactivó"
    print(f"[AUDIT] {datetime.now()}: Usuario {current_user.email} {action} usuario {user.email}")
    
    return UserResponse.model_validate(user)


@router.post(
    "/users/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    summary="Restablecer contraseña",
    description="Genera una nueva contraseña temporal para un usuario",
    tags=["Gestión de Usuarios"]
)
async def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera una nueva contraseña temporal para un usuario
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        PasswordResetResponse: Contraseña temporal generada
        
    Raises:
        HTTPException: Si el usuario no existe
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Generar nueva contraseña temporal
    temp_password = generate_temporary_password()
    user.password_hash = get_password_hash(temp_password)
    
    db.commit()
    
    # Log de auditoría
    print(f"[AUDIT] {datetime.now()}: Usuario {current_user.email} restableció contraseña de {user.email}")
    
    return PasswordResetResponse(
        message="Nueva contraseña generada exitosamente",
        temporary_password=temp_password
    )


@router.patch(
    "/users/{user_id}/password",
    response_model=UserResponse,
    summary="Actualizar contraseña",
    description="Actualiza la contraseña de un usuario con una contraseña manual",
    tags=["Gestión de Usuarios"]
)
async def update_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza la contraseña de un usuario
    
    Args:
        user_id: ID del usuario
        password_data: Datos con la nueva contraseña
        db: Sesión de base de datos
        current_user: Usuario autenticado
        
    Returns:
        UserResponse: Usuario actualizado
        
    Raises:
        HTTPException: Si el usuario no existe o la contraseña es inválida
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    new_password = password_data.get('password')
    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña requerida"
        )
    
    # Validar seguridad de contraseña (ISO 27001)
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    if not any(c.isupper() for c in new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una mayúscula"
        )
    if not any(c.islower() for c in new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos una minúscula"
        )
    if not any(c.isdigit() for c in new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe contener al menos un número"
        )
    
    # Actualizar contraseña
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    
    # Log de auditoría
    print(f"[AUDIT] {datetime.now()}: Usuario {current_user.email} actualizó contraseña de {user.email}")
    
    return UserResponse.model_validate(user)
