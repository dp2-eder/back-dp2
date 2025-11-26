"""
Registro centralizado de routers de la aplicación.

Gestiona la carga dinámica y registro de todos los controladores de la API.
"""

import importlib
import logging
from typing import List, Tuple

from fastapi import FastAPI, APIRouter

logger = logging.getLogger(__name__)


# Configuración de controladores: (módulo, tag)
CONTROLLERS: List[Tuple[str, str]] = [
    ("src.api.controllers.login_controller", "Login"),
    ("src.api.controllers.admin_sesiones_controller", "Admin - Sesiones"),
    ("src.api.controllers.auth_controller", "Autenticación"),
    ("src.api.controllers.rol_controller", "Roles"),
    ("src.api.controllers.local_controller", "Locales"),
    ("src.api.controllers.zona_controller", "Zonas"),
    ("src.api.controllers.sesion_controller", "Sesiones"),
    ("src.api.controllers.sesion_mesa_controller", "Sesiones de Mesa"),
    ("src.api.controllers.categoria_controller", "Categorías"),
    ("src.api.controllers.alergeno_controller", "Alérgenos"),
    ("src.api.controllers.producto_controller", "Productos"),
    ("src.api.controllers.tipo_opciones_controller", "Tipos de Opciones"),
    ("src.api.controllers.producto_opcion_controller", "Producto Opciones"),
    ("src.api.controllers.producto_opciones_manage_controller", "Gestión de Opciones de Productos"),
    ("src.api.controllers.sync_controller", "Sincronización"),
    ("src.api.controllers.mesa_controller", "Mesas"),
    ("src.api.controllers.pedido_controller", "Pedidos"),
    ("src.api.controllers.pedido_producto_controller", "Pedidos Productos"),
    ("src.api.controllers.pedido_opcion_controller", "Pedido Opciones"),
    ("src.api.controllers.locales_categorias_controller", "Local - Categorías"),
    ("src.api.controllers.locales_productos_controller", "Local - Productos"),
    ("src.api.controllers.locales_tipos_opciones_controller", "Local - Tipos de Opciones"),
    ("src.api.controllers.locales_productos_opciones_controller", "Local - Opciones de Productos"),
    ("src.api.controllers.admin_controller", "Administrator"),
]

API_PREFIX = "/api/v1"


def register_routers(app: FastAPI) -> None:
    """
    Registra todos los routers de la aplicación.

    Carga dinámicamente los controladores y los registra con la aplicación FastAPI.

    Parameters
    ----------
    app : FastAPI
        La instancia de la aplicación FastAPI donde registrar los routers
    """
    for module_name, tag in CONTROLLERS:
        try:
            module = importlib.import_module(module_name)
            router = getattr(module, "router", None)

            if router and isinstance(router, APIRouter):
                app.include_router(router, prefix=API_PREFIX)
                logger.info(f"Router '{tag}' registrado correctamente")
            else:
                logger.warning(f"No se encontró un router válido en {module_name}")
        except Exception as e:
            logger.error(f"Error al cargar el controlador {module_name}: {e}")
            logger.exception("Traceback completo:")
