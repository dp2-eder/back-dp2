"""
Gestión del ciclo de vida de la aplicación FastAPI.

Controla la inicialización y limpieza de recursos del sistema.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.core.database import create_tables, close_database
from src.core.logging import configure_logging

logger = logging.getLogger(__name__)


def _ensure_static_directories() -> None:
    """Verifica y crea los directorios estáticos necesarios."""
    from src.business_logic.menu.producto_img_service import ProductoImagenService
    
    ProductoImagenService.ensure_directory_exists()
    logger.info(f"Directorio de imágenes verificado: {ProductoImagenService.STATIC_DIR}")


async def _initialize_database() -> None:
    """Inicializa las tablas de la base de datos."""
    import asyncio
    
    await create_tables()
    logger.info("Tablas de base de datos inicializadas")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación FastAPI.

    Controla los eventos de inicio y apagado de la aplicación,
    configurando recursos necesarios al inicio y liberándolos al finalizar.

    Parameters
    ----------
    app : FastAPI
        La instancia de la aplicación FastAPI
    """
    # ========== Inicialización ==========
    logger.info("Iniciando Restaurant Backend API...")
    
    configure_logging()
    _ensure_static_directories()
    await _initialize_database()
    
    logger.info("Restaurant Backend API iniciada correctamente")

    yield  # La aplicación está en funcionamiento

    # ========== Limpieza ==========
    logger.info("Cerrando Restaurant Backend API...")
    
    await close_database()
    
    logger.info("Recursos liberados correctamente")
