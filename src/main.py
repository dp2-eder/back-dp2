"""
Punto de entrada principal de la aplicación FastAPI.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import get_settings
from src.core.dependencies import ErrorHandlerMiddleware
from src.core.app_lifespan import lifespan
from src.core.router_registry import register_routers
from src.core.model_registry import register_all_models

# Registrar modelos ANTES de importar controladores
register_all_models()

logger = logging.getLogger(__name__)


def _mount_static_files(app: FastAPI) -> None:
    """Monta los archivos estáticos de la aplicación."""
    static_dir = Path("app/static/images")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Directorio estático montado: {static_dir}")
    else:
        logger.warning(f"Directorio estático no encontrado: {static_dir}")


def _configure_middleware(app: FastAPI, settings) -> None:
    """Configura los middlewares de la aplicación."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )
    app.add_middleware(ErrorHandlerMiddleware)


def _register_health_endpoints(app: FastAPI, settings) -> None:
    """Registra endpoints de salud y raíz."""

    @app.get("/")
    async def root():
        """Endpoint raíz de la API."""
        return {
            "message": "Restaurant Backend API",
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health")
    async def health_check():
        """Endpoint de verificación de salud del sistema."""
        return {
            "status": "healthy",
            "service": "restaurant-backend",
            "version": settings.app_version,
            "environment": settings.environment,
        }


def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.

    Returns
    -------
    FastAPI
        Instancia configurada de la aplicación FastAPI
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    _mount_static_files(app)
    _configure_middleware(app, settings)
    register_routers(app)
    _register_health_endpoints(app, settings)

    return app


# Crear la instancia de la aplicación
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    logger.info(f"Iniciando servidor en {settings.host}:{settings.port}")
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
