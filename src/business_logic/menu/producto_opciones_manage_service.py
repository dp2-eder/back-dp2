"""
Servicio para gestionar las opciones de productos (secciones y complementos).
"""

from typing import List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.repositories.menu.producto_repository import ProductoRepository
from src.repositories.pedidos.tipo_opciones_repository import TipoOpcionRepository
from src.repositories.pedidos.producto_opcion_repository import ProductoOpcionRepository
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
from src.api.schemas.producto_opciones_manage_schema import (
    AgregarOpcionesProductoRequest,
    AgregarOpcionesProductoResponse,
    OpcionesProductoListResponse,
    SeccionOpcionesResponse,
    OpcionComplementoResponse,
)
from src.business_logic.exceptions.producto_exceptions import ProductoNotFoundError


class ProductoOpcionesManageService:
    """Servicio para gestionar secciones de opciones y complementos de productos."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.producto_repository = ProductoRepository(session)
        self.tipo_opcion_repository = TipoOpcionRepository(session)
        self.producto_opcion_repository = ProductoOpcionRepository(session)

    