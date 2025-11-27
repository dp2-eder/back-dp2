"""
Inicialización de la base de datos con datos por defecto.

Este módulo proporciona funcionalidad para poblar la base de datos con datos
iniciales necesarios para el funcionamiento del sistema. Se ejecuta solo una vez
cuando la base de datos está vacía.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.core.security import security
from src.models.auth.rol_model import RolModel
from src.models.auth.admin_model import AdminModel
from src.models.menu.alergeno_model import AlergenoModel
from src.models.menu.categoria_model import CategoriaModel
from src.models.mesas.local_model import LocalModel
from src.core.enums.alergeno_enums import NivelRiesgo
from src.core.enums.local_enums import TipoLocal

logger = logging.getLogger(__name__)


# ==================== Datos por defecto ====================

DEFAULT_ROLES = [
    {
        "nombre": "CLIENTE",
        "descripcion": "Usuario cliente del restaurante con acceso temporal",
        "activo": True,
        "es_default": True,
    },
    {
        "nombre": "ADMINISTRADOR",
        "descripcion": "Administrador del sistema con acceso completo",
        "activo": True,
        "es_default": False,
    },
]

DEFAULT_ADMIN = {
    "usuario": "admin",
    "email": "admin@admin.com",
    "password": "admin",
}

DEFAULT_ALERGENOS = [
    {
        "nombre": "Cereales con Gluten",
        "descripcion": "Trigo, centeno, cebada, avena, espelta, kamut o sus variedades híbridas",
        "icono": "🌾",
        "nivel_riesgo": NivelRiesgo.ALTO,
        "activo": True,
    },
    {
        "nombre": "Crustáceos",
        "descripcion": "Crustáceos y productos a base de crustáceos",
        "icono": "🦐",
        "nivel_riesgo": NivelRiesgo.CRITICO,
        "activo": True,
    },
    {
        "nombre": "Huevos",
        "descripcion": "Huevos y productos derivados del huevo",
        "icono": "🥚",
        "nivel_riesgo": NivelRiesgo.MEDIO,
        "activo": True,
    },
    {
        "nombre": "Pescado",
        "descripcion": "Pescado y productos a base de pescado",
        "icono": "🐟",
        "nivel_riesgo": NivelRiesgo.ALTO,
        "activo": True,
    },
    {
        "nombre": "Cacahuetes",
        "descripcion": "Cacahuetes y productos a base de cacahuetes",
        "icono": "🥜",
        "nivel_riesgo": NivelRiesgo.CRITICO,
        "activo": True,
    },
    {
        "nombre": "Soja",
        "descripcion": "Soja y productos a base de soja",
        "icono": "🫘",
        "nivel_riesgo": NivelRiesgo.MEDIO,
        "activo": True,
    },
    {
        "nombre": "Leche y Lácteos",
        "descripcion": "Leche y sus derivados, incluida la lactosa",
        "icono": "🥛",
        "nivel_riesgo": NivelRiesgo.MEDIO,
        "activo": True,
    },
    {
        "nombre": "Frutos de Cáscara",
        "descripcion": "Almendras, avellanas, nueces, anacardos, pacanas, castañas de Pará, pistachos, nueces de macadamia y productos derivados",
        "icono": "🌰",
        "nivel_riesgo": NivelRiesgo.CRITICO,
        "activo": True,
    },
    {
        "nombre": "Apio",
        "descripcion": "Apio y productos derivados del apio",
        "icono": "🥬",
        "nivel_riesgo": NivelRiesgo.BAJO,
        "activo": True,
    },
    {
        "nombre": "Mostaza",
        "descripcion": "Mostaza y productos a base de mostaza",
        "icono": "🌭",
        "nivel_riesgo": NivelRiesgo.BAJO,
        "activo": True,
    },
    {
        "nombre": "Sésamo",
        "descripcion": "Granos o semillas de sésamo y productos a base de sésamo",
        "icono": "⚪",
        "nivel_riesgo": NivelRiesgo.ALTO,
        "activo": True,
    },
    {
        "nombre": "Sulfitos",
        "descripcion": "Dióxido de azufre y sulfitos en concentraciones superiores a 10 mg/kg o 10 mg/l",
        "icono": "💨",
        "nivel_riesgo": NivelRiesgo.MEDIO,
        "activo": True,
    },
    {
        "nombre": "Altramuces",
        "descripcion": "Altramuces y productos a base de altramuces",
        "icono": "🫘",
        "nivel_riesgo": NivelRiesgo.BAJO,
        "activo": True,
    },
    {
        "nombre": "Moluscos",
        "descripcion": "Moluscos y productos a base de moluscos",
        "icono": "🦑",
        "nivel_riesgo": NivelRiesgo.ALTO,
        "activo": True,
    },
]

DEFAULT_LOCAL = {
    "codigo": "BA-001",
    "nombre": "La Cevichería Central",
    "direccion": "Av. Principal 123",
    "distrito": "Miraflores",
    "ciudad": "Lima",
    "telefono": "+51 1 234-5678",
    "email": "central@lacevicheria.com",
    "tipo_local": TipoLocal.CENTRAL,
    "capacidad_total": 80,
    "activo": True,
}


# ==================== Funciones de inicialización ====================


async def _create_roles(session: AsyncSession) -> None:
    """Crea los roles por defecto del sistema."""
    logger.info("Verificando roles del sistema...")

    result = await session.execute(select(RolModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("Roles ya existen, omitiendo creación")
        return

    for rol_data in DEFAULT_ROLES:
        rol = RolModel(**rol_data)
        session.add(rol)

    await session.commit()
    logger.info(f"Roles creados exitosamente: {len(DEFAULT_ROLES)}")


async def _create_default_admin(session: AsyncSession) -> None:
    """Crea el administrador por defecto del sistema."""
    logger.info("Verificando administrador por defecto...")
    result = await session.execute(select(AdminModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("Administrador ya existe, omitiendo creación")
        return

    admin_data = DEFAULT_ADMIN.copy()
    admin_data["password"] = security.get_password_hash(admin_data["password"])

    admin = AdminModel(**admin_data)
    session.add(admin)

    await session.commit()
    logger.info(f"Administrador por defecto creado: {DEFAULT_ADMIN['usuario']}")


async def _create_alergenos(session: AsyncSession) -> None:
    """Crea los alérgenos por defecto del sistema."""
    logger.info("Verificando alérgenos del sistema...")

    result = await session.execute(select(AlergenoModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("Alérgenos ya existen, omitiendo creación")
        return

    for alergeno_data in DEFAULT_ALERGENOS:
        alergeno = AlergenoModel(**alergeno_data)
        session.add(alergeno)

    await session.commit()
    logger.info(f"Alérgenos creados exitosamente: {len(DEFAULT_ALERGENOS)}")


async def _create_default_local(session: AsyncSession) -> None:
    """Crea el local central por defecto."""
    logger.info("Verificando local por defecto...")

    result = await session.execute(select(LocalModel).limit(1))
    if result.scalar_one_or_none():
        logger.info("Local ya existe, omitiendo creación")
        return

    local = LocalModel(**DEFAULT_LOCAL)
    session.add(local)

    await session.commit()
    logger.info(f"Local por defecto creado: {DEFAULT_LOCAL['nombre']}")


async def _is_database_empty(session: AsyncSession) -> bool:
    """
    Verifica si la base de datos está vacía.

    Revisa las tablas principales para determinar si la BD necesita inicialización.

    Parameters
    ----------
    session : AsyncSession
        Sesión de base de datos activa

    Returns
    -------
    bool
        True si la base de datos está vacía, False en caso contrario
    """
    roles_result = await session.execute(select(RolModel).limit(1))
    admins_result = await session.execute(select(AdminModel).limit(1))

    has_roles = roles_result.scalar_one_or_none() is not None
    has_admins = admins_result.scalar_one_or_none() is not None

    return not (has_roles or has_admins)


async def database_initialization() -> None:
    """
    Inicializa la base de datos con datos por defecto.

    Esta función es idempotente y segura de ejecutar múltiples veces.
    Solo crea datos si la base de datos está vacía.

    Se ejecuta automáticamente durante el ciclo de vida de la aplicación.
    """
    try:
        async with get_session() as session:
            if not await _is_database_empty(session):
                logger.info("Base de datos ya contiene datos, omitiendo inicialización")
                return

            await _create_roles(session)
            await _create_default_admin(session)
            await _create_alergenos(session)
            await _create_default_local(session)

            logger.info("Base de datos inicializada exitosamente")

    except Exception as e:
        logger.error(f"Error durante la inicialización de la base de datos: {e}")
        raise
