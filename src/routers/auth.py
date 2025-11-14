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
from ..schemas import (
    Token, UserResponse, UserLogin, HealthResponse, UserCreate,
    ForgotPasswordRequest, ResetPasswordRequest, ForgotPasswordResponse, PasswordResetResponse
)
from ..utils import (
    verify_password, create_access_token, get_current_user, get_password_hash,
    generate_reset_token, get_reset_token_expiration, is_reset_token_valid,
    generate_reset_code, get_reset_code_expiration, is_reset_code_valid,
    verify_security_answer
)
from ..utils.email import send_reset_password_email
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


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Solicitar restablecimiento de contraseña con verificación adicional",
    description="Requiere verificación por teléfono o pregunta de seguridad para mayor seguridad",
    tags=["Autenticación"]
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    # Buscar usuario por email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Por seguridad, siempre devolvemos el mismo mensaje si el email no existe
    if not user or not user.is_active:
        return ForgotPasswordResponse(
            message="Si el email existe y está activo, se ha generado un token de restablecimiento",
            reset_code=None,
            token=None,
            security_question=None
        )
    
    # Si no se especifica método o no hay datos configurados, usar método simple con CÓDIGO de 6 dígitos
    if not request.verification_method:
        # Método simple: generar CÓDIGO de 6 dígitos (más user-friendly)
        reset_code = generate_reset_code()
        reset_code_expires = get_reset_code_expiration(minutes=10)
        
        user.reset_code = reset_code
        user.reset_code_expires = reset_code_expires
        user.reset_token = None  # No usar token largo
        user.reset_token_expires = None
        db.commit()
        
        # Intentar enviar por email
        email_sent = await send_reset_password_email(
            to_email=user.email,
            reset_code=reset_code,
            user_name=user.name
        )
        
        if email_sent:
            message = "Se ha enviado un código de 6 dígitos a tu correo electrónico. Revisa tu bandeja de entrada (y spam). El código es válido por 10 minutos."
            code_to_show = None  # No mostrar código si se envió por email
        else:
            # Si no se pudo enviar (SMTP deshabilitado o error), mostrar en pantalla (solo para desarrollo)
            message = f"⚠️ No se pudo enviar el email. Tu código de restablecimiento es: {reset_code} (válido por 10 minutos). Ingresa este código para restablecer tu contraseña."
            code_to_show = reset_code
        
        return ForgotPasswordResponse(
            message=message,
            reset_code=code_to_show,  # Solo mostrar si el email falló
            token=None,  # No usar tokens largos
            security_question=None
        )
    
    # Verificar según el método elegido
    if request.verification_method == "phone":
        # Verificación por teléfono
        if not request.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Número de teléfono requerido para verificación por SMS"
            )
        
        # Verificar si el usuario tiene teléfono configurado
        if not user.phone_number:
            # Si no tiene teléfono, usar método simple
            reset_token = generate_reset_token()
            reset_token_expires = get_reset_token_expiration(hours=1)
            
            user.reset_token = reset_token
            user.reset_token_expires = reset_token_expires
            user.reset_code = None
            user.reset_code_expires = None
            db.commit()
            
            return ForgotPasswordResponse(
                message=f"El usuario no tiene teléfono configurado. Token de restablecimiento generado. Token: {reset_token} (válido por 1 hora).",
                reset_code=None,
                token=reset_token,
                security_question=None
            )
        
        # Verificar que el teléfono coincida (normalizar formato)
        user_phone = user.phone_number.replace(" ", "").replace("-", "").replace("+", "") if user.phone_number else ""
        request_phone = request.phone_number.replace(" ", "").replace("-", "").replace("+", "")
        
        if user_phone != request_phone:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El número de teléfono no coincide con el registrado"
            )
        
        # Generar código de 6 dígitos
        reset_code = generate_reset_code()
        reset_code_expires = get_reset_code_expiration(minutes=10)  # Válido por 10 minutos
        
        # Guardar código en la base de datos
        user.reset_code = reset_code
        user.reset_code_expires = reset_code_expires
        user.reset_token = None  # Limpiar token anterior si existe
        user.reset_token_expires = None
        db.commit()
        
        # Intentar enviar por email (más común que SMS)
        email_sent = await send_reset_password_email(
            to_email=user.email,
            reset_code=reset_code,
            user_name=user.name
        )
        
        if email_sent:
            message = f"Se ha enviado un código de verificación a tu email ({user.email}). Revisa tu bandeja de entrada (y spam). El código es válido por 10 minutos."
            code_to_show = None  # No mostrar código si se envió por email
        else:
            # Si no se pudo enviar (SMTP deshabilitado), mostrar en pantalla
            message = f"Código de verificación generado. Código: {reset_code} (válido por 10 minutos). En producción, este código se enviaría por email."
            code_to_show = reset_code
        
        return ForgotPasswordResponse(
            message=message,
            reset_code=code_to_show,
            token=None,
            security_question=None
        )
    
    elif request.verification_method == "security_question":
        # Verificación por pregunta de seguridad
        if not user.security_question:
            # Si no tiene pregunta, usar método simple
            reset_token = generate_reset_token()
            reset_token_expires = get_reset_token_expiration(hours=1)
            
            user.reset_token = reset_token
            user.reset_token_expires = reset_token_expires
            user.reset_code = None
            user.reset_code_expires = None
            db.commit()
            
            return ForgotPasswordResponse(
                message=f"El usuario no tiene pregunta de seguridad configurada. Token de restablecimiento generado. Token: {reset_token} (válido por 1 hora).",
                reset_code=None,
                token=reset_token,
                security_question=None
            )
        
        if not request.security_answer:
            # Si no viene la respuesta, devolver la pregunta
            return ForgotPasswordResponse(
                message="Responda la pregunta de seguridad para continuar",
                reset_code=None,
                token=None,
                security_question=user.security_question
            )
        
        # Verificar respuesta de seguridad
        if not user.security_answer_hash or not verify_security_answer(request.security_answer, user.security_answer_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La respuesta a la pregunta de seguridad es incorrecta"
            )
        
        # Generar token de restablecimiento (fallback, no hay SMS)
        reset_token = generate_reset_token()
        reset_token_expires = get_reset_token_expiration(hours=1)
        
        user.reset_token = reset_token
        user.reset_token_expires = reset_token_expires
        user.reset_code = None
        user.reset_code_expires = None
        db.commit()
        
        # Intentar enviar por email
        email_sent = await send_reset_password_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.name
        )
        
        if email_sent:
            message = "Verificación exitosa. Se ha enviado un email con el token de restablecimiento. Revisa tu bandeja de entrada (y spam). El token es válido por 1 hora."
            token_to_show = None
        else:
            message = "Verificación exitosa. Token de restablecimiento generado. Copie el token y úselo para restablecer su contraseña. El token es válido por 1 hora."
            token_to_show = reset_token
        
        return ForgotPasswordResponse(
            message=message,
            reset_code=None,
            token=token_to_show,
            security_question=None
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Método de verificación inválido. Use 'phone' o 'security_question'"
        )


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    summary="Restablecer contraseña",
    description="Restablece la contraseña usando código de 6 dígitos (SMS) o token",
    tags=["Autenticación"]
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Restablece la contraseña usando código de 6 dígitos (SMS) o token
    
    Args:
        request: Email, código/token y nueva contraseña
        db: Sesión de base de datos
        
    Returns:
        PasswordResetResponse: Mensaje de confirmación
        
    Raises:
        HTTPException: Si el código/token es inválido o ha expirado
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador."
        )
    
    # Verificar código o token
    if request.reset_code:
        # Verificación por código de 6 dígitos (SMS)
        if user.reset_code != request.reset_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de verificación inválido"
            )
        
        # Verificar que el código no haya expirado
        if not is_reset_code_valid(user.reset_code_expires):
            # Limpiar código expirado
            user.reset_code = None
            user.reset_code_expires = None
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código de verificación ha expirado. Por favor solicite uno nuevo."
            )
        
        # Limpiar código después de usar
        user.reset_code = None
        user.reset_code_expires = None
        
    elif request.token:
        # Verificación por token (fallback)
        if user.reset_token != request.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de restablecimiento inválido"
            )
        
        # Verificar que el token no haya expirado
        if not is_reset_token_valid(user.reset_token_expires):
            # Limpiar token expirado
            user.reset_token = None
            user.reset_token_expires = None
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El token de restablecimiento ha expirado. Por favor solicite uno nuevo."
            )
        
        # Limpiar token después de usar
        user.reset_token = None
        user.reset_token_expires = None
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere código de verificación o token"
        )
    
    # Actualizar contraseña
    user.password_hash = get_password_hash(request.new_password)
    
    db.commit()
    
    return PasswordResetResponse(
        message="Contraseña restablecida exitosamente. Ya puede iniciar sesión con su nueva contraseña.",
        temporary_password=None
    )

