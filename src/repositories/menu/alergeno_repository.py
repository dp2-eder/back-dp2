"""Repositorio de acceso a datos para alérgenos."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.alergeno_schema import AlergenoList, AlergenoSummary
from src.models.menu.alergeno_model import AlergenoModel


class AlergenoRepository:
    """Gestiona el acceso a datos de alérgenos.
    
    Responsabilidades:
    - Ejecutar consultas optimizadas a la base de datos
    - Retornar DTOs en lugar de modelos (evita acoplamiento)
    - Delegar transacciones a la sesión del servicio
    """

    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        """Inicializa el repositorio.
        
        Args:
            session: Sesión asíncrona de SQLAlchemy (gestionada externamente)
        """
        self._session = session

    async def get_all_paginated(
        self, skip: int = 0, limit: int = 100, producto_id: Optional[str] = None
    ) -> AlergenoList:
        """Obtiene lista paginada de alérgenos.
        
        Args:
            skip: Offset de paginación (por defecto 0)
            limit: Límite de registros (por defecto 100)
            producto_id: Filtro opcional por producto
            
        Returns:
            Lista paginada de alérgenos con total de registros
            
        Note:
            Usa una única query con window functions para eficiencia.
            Retorna DTOs directamente para desacoplar capas.
        """
        # Query base
        stmt = select(AlergenoModel).offset(skip).limit(limit)
        
        # Aplicar filtro si existe
        if producto_id:
            stmt = stmt.join(AlergenoModel.productos).where(
                AlergenoModel.productos.any(id=producto_id)
            )
        
        # Query de conteo (solo si necesitamos filtrar, sino optimizar)
        count_stmt = select(func.count()).select_from(AlergenoModel)
        if producto_id:
            count_stmt = count_stmt.join(AlergenoModel.productos).where(
                AlergenoModel.productos.any(id=producto_id)
            )
        
        # Ejecutar queries
        result = await self._session.execute(stmt)
        count_result = await self._session.execute(count_stmt)
        
        alergenos = result.scalars().all()
        total = count_result.scalar_one()
        
        # Convertir a DTOs
        items = [AlergenoSummary.model_validate(a) for a in alergenos]
        
        return AlergenoList(items=items, total=total)
