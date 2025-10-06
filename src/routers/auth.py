"""
Router de Autenticación
Endpoints: /login, /me, /health
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models import get_db, User
from ..schemas import Token, UserResponse, UserLogin, HealthResponse, UserCreate
from ..utils import verify_password, create_access_token, get_current_user, get_password_hash
from ..config import settings

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    description="Autentica un usuario y devuelve un token JWT válido por 24 horas",
    tags=["Autenticación"]
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    HU0: Como administrador, quiero iniciar sesión con mis credenciales
    
    Args:
        credentials: Email y contraseña del usuario
        db: Sesión de base de datos
        
    Returns:
        Token: Token JWT con información del usuario
        
    Raises:
        HTTPException: Si las credenciales son incorrectas
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador.",
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Retornar token y información del usuario
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # En segundos
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener usuario actual",
    description="Devuelve la información del usuario autenticado",
    tags=["Autenticación"]
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la información del usuario autenticado
    
    Args:
        current_user: Usuario actual (inyectado por dependency)
        
    Returns:
        UserResponse: Información del usuario
    """
    return UserResponse.model_validate(current_user)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica el estado del servicio y la conexión a base de datos",
    tags=["Health"]
)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check del microservicio
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        HealthResponse: Estado del servicio
    """
    # Verificar conexión a base de datos
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy" if database_status == "connected" else "unhealthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        database=database_status
    )


@router.post(
    "/register",
    response_model=UserResponse,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario administrador (solo para desarrollo)",
    tags=["Autenticación"],
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_active_admin)  # Descomentar en producción
):
    """
    Registra un nuevo usuario en el sistema
    NOTA: En producción, este endpoint debe requerir autenticación de admin
    
    Args:
        user_data: Datos del nuevo usuario
        db: Sesión de base de datos
        
    Returns:
        UserResponse: Usuario creado
        
    Raises:
        HTTPException: Si el email ya existe
    """
    # Verificar que el email no exista
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear nuevo usuario
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)


@router.post(
    "/logout",
    summary="Cerrar sesión",
    description="Cierra la sesión del usuario (cliente debe eliminar el token)",
    tags=["Autenticación"]
)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Cierra la sesión del usuario
    Nota: Como usamos JWT stateless, el cliente debe eliminar el token
    
    Args:
        current_user: Usuario actual
        
    Returns:
        dict: Mensaje de confirmación
    """
    return {
        "message": "Sesión cerrada exitosamente",
        "detail": "Por favor elimine el token del cliente"
    }

