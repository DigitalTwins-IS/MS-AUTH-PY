"""
MS-AUTH-PY - Microservicio de Autenticación
FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .routers import auth_router

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Microservicio de autenticación para el Sistema Digital Twins.
    
    ## Funcionalidades
    
    * **Login**: Autenticación con email y contraseña
    * **JWT**: Generación de tokens de acceso
    * **Me**: Obtener información del usuario autenticado
    * **Health**: Verificación del estado del servicio
    
    ## Historias de Usuario Implementadas
    
    * **HU0**: Como administrador, quiero iniciar sesión con mis credenciales
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(
    auth_router,
    prefix=settings.API_PREFIX,
    tags=["auth"]
)


@app.get("/", include_in_schema=False)
async def root():
    """Redireccionar a la documentación"""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
async def root_health():
    """Health check raíz"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} iniciado")
    print(f"📚 Documentación disponible en: http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/docs")
    print(f"🔐 Endpoints de autenticación en: {settings.API_PREFIX}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    print(f"🛑 {settings.APP_NAME} detenido")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG
    )

