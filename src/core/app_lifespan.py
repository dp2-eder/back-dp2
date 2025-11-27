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
from src.business_logic.notifications.rabbitmq_service import get_rabbitmq_service, close_rabbitmq_service

logger = logging.getLogger(__name__)


def _ensure_static_directories() -> None:
    """Verifica y crea los directorios estáticos necesarios."""
    from src.business_logic.menu.imagen_service import ImagenService
    
    ImagenService.ensure_directory_exists()
    logger.info(f"Directorio de imágenes verificado: {ImagenService.STATIC_DIR}")


async def _initialize_database() -> None:
    """Inicializa las tablas de la base de datos y carga datos por defecto."""
    from src.core.init_db import database_initialization
    await create_tables()
    logger.info("Tablas de base de datos inicializadas")
    await database_initialization()


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

    # Iniciar RabbitMQ y consumidor
    try:
        rabbitmq = await get_rabbitmq_service()
        await rabbitmq.start_screenshot_consumer()
    except Exception as e:
        logger.error(f"Error al iniciar RabbitMQ: {e}")
    
    logger.info("Restaurant Backend API iniciada correctamente")

    yield  # La aplicación está en funcionamiento

    # ========== Limpieza ==========
    logger.info("Cerrando Restaurant Backend API...")
    
    await close_rabbitmq_service()
    await close_database()
    
    logger.info("Recursos liberados correctamente")
