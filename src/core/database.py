"""
Configuración y gestión de conexiones a la base de datos.

Implementa el patrón moderno de gestión de conexiones async con SQLAlchemy 2.0+
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)

from src.core.config import get_settings
from src.models.base_model import BaseModel


def _create_engine() -> AsyncEngine:
    """Crea el motor de base de datos con configuración apropiada."""
    settings = get_settings()

    is_sqlite = settings.database_url.startswith("sqlite")

    if is_sqlite:
        return create_async_engine(
            settings.database_url,
            echo=settings.debug,
            future=True,
        )

    # MySQL, PostgreSQL, etc. con pooling completo
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        future=True,
    )


# Instancia global del engine
engine: AsyncEngine = _create_engine()

# Factory de sesiones
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ==================== Dependency Injection ====================
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para inyección de sesión de base de datos.

    Yields
    ------
    AsyncSession
        Sesión de base de datos lista para usar

    Examples
    --------
    ```python
    @router.get("/items")
    async def get_items(session: AsyncSession = Depends(get_database_session)):
        result = await session.execute(select(ItemModel))
        return result.scalars().all()
    ```
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager para uso fuera de FastAPI (scripts, tests, etc.)."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==================== Lifecycle Management ====================
async def create_tables() -> None:
    """
    Crea todas las tablas definidas en el modelo de datos.

    Los modelos ya están registrados por model_registry.
    """
    from src.core.model_registry import register_all_models

    register_all_models()

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def drop_tables() -> None:
    """
    Elimina todas las tablas de la base de datos.

    ⚠️ Usar solo en entornos de desarrollo/testing.
    """
    from src.core.model_registry import register_all_models

    register_all_models()

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


async def close_database() -> None:
    """
    Cierra la conexión a la base de datos y libera recursos.

    Debe llamarse al finalizar la aplicación.
    """
    await engine.dispose()
