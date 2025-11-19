"""
Repositorio para la gestión de mesas en el sistema.
"""

from typing import Optional, List, Tuple, Dict, Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload, joinedload

from src.models.menu.alergeno_model import AlergenoModel
from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.local_model import LocalModel


class MesaRepository:
    async def batch_delete(self, mesa_ids: List[str]) -> int:
        """
        Elimina múltiples mesas por sus IDs en una sola operación batch.

        Parameters
        ----------
        mesa_ids : List[str]
            Lista de IDs de las mesas a eliminar.

        Returns
        -------
        int
            Número de mesas eliminadas.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        if not mesa_ids:
            return 0
        try:
            stmt = delete(MesaModel).where(MesaModel.id.in_(mesa_ids))
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount
        except SQLAlchemyError:
            await self.session.rollback()
            raise
    """Repositorio para gestionar operaciones CRUD del modelo de mesas.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las mesas en el sistema, siguiendo el patrón Repository.

    Attributes
    ----------
    session : AsyncSession
        Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
    """    

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.session = session

    async def create(self, mesa: MesaModel) -> MesaModel:
        """
        Crea una nueva mesa en la base de datos.

        Parameters
        ----------
        mesa : MesaModel
            Instancia del modelo de mesa a crear.

        Returns
        -------
        MesaModel
            El modelo de mesa creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(mesa)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(mesa)
            return mesa
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, mesa_id: str) -> Optional[MesaModel]:
        """
        Obtiene una mesa por su identificador único.

        Parameters
        ----------
        mesa_id : str
            Identificador único de la mesa a buscar.

        Returns
        -------
        Optional[MesaModel]
            La mesa encontrada o None si no existe.
        """
        query = select(MesaModel).where(MesaModel.id == mesa_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_numero(self, numero: str) -> Optional[MesaModel]:
        """
        Obtiene una mesa por su número.

        Parameters
        ----------
        numero : str
            Número de la mesa a buscar.

        Returns
        -------
        Optional[MesaModel]
            La mesa encontrada o None si no existe.
        """
        query = (
            select(MesaModel)
            .where(MesaModel.numero == numero)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, mesa_id: str) -> bool:
        """
        Elimina una mesa de la base de datos por su ID.

        Parameters
        ----------
        mesa_id : str
            Identificador único de la mesa a eliminar.

        Returns
        -------
        bool
            True si la mesa fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(MesaModel).where(MesaModel.id == mesa_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, mesa_id: str, **kwargs) -> Optional[MesaModel]:
        """
        Actualiza una mesa existente con los valores proporcionados.

        Parameters
        ----------
        mesa_id : str
            Identificador único de la mesa a actualizar.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[MesaModel]
            La mesa actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(MesaModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(mesa_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(MesaModel)
                .where(MesaModel.id == mesa_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar la mesa actualizada
            updated_mesa = await self.get_by_id(mesa_id)

            # Si no se encontró la mesa, retornar None
            if not updated_mesa:
                return None

            return updated_mesa
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
            self, 
            skip: int = 0, 
            limit: int = 100,
        ) -> Tuple[List[MesaModel], int]:
        """
        Obtiene todas las mesas con paginación.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[MesaModel], int]
            Tupla con la lista de mesas y el número total de registros.
        """

        # Consulta para obtener las mesas paginadas
        query = select(MesaModel).offset(skip).limit(limit)
        # Consulta para obtener el total de registros
        count_query = select(func.count(MesaModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            mesas = result.scalars().all()
            total = count_result.scalar() or 0

            return list(mesas), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise

    async def get_all_with_local(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[MesaModel], int]:
        """
        Obtiene todas las mesas con paginación, incluyendo información del local (via zona).

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[MesaModel], int]
            Tupla con la lista de mesas (con local eager-loaded) y el número total de registros.
        """
        # Consulta con eager loading de zona y local
        query = (
            select(MesaModel)
            .options(
                joinedload(MesaModel.zona).joinedload(ZonaModel.local)
            )
            .offset(skip)
            .limit(limit)
        )
        # Consulta para obtener el total de registros
        count_query = select(func.count(MesaModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            mesas = result.scalars().unique().all()
            total = count_result.scalar() or 0

            return list(mesas), total
        except SQLAlchemyError:
            raise

    async def get_local_by_mesa_id(self, mesa_id: str) -> Optional[LocalModel]:
        """
        Obtiene el local asociado a una mesa (via zona).

        Parameters
        ----------
        mesa_id : str
            ID de la mesa.

        Returns
        -------
        Optional[LocalModel]
            El local asociado a la mesa o None si no existe.
        """
        query = (
            select(LocalModel)
            .join(ZonaModel, LocalModel.id == ZonaModel.id_local)
            .join(MesaModel, ZonaModel.id == MesaModel.id_zona)
            .where(MesaModel.id == mesa_id)
        )

        try:
            result = await self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError:
            raise

    async def batch_insert(self, mesas: List[MesaModel]) -> List[MesaModel]:
        """
        Inserta múltiples mesas en la base de datos en una sola operación.

        Parameters
        ----------
        mesas : List[MesaModel]
            Lista de instancias de mesas a insertar.

        Returns
        -------
        List[MesaModel]
            Lista de las mesas insertadas con sus IDs asignados.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        if not mesas:
            return []
            
        try:
            # Agregar todos los mesas a la sesión
            self.session.add_all(mesas)

            # Flush para generar los IDs y otras columnas generadas automáticamente
            await self.session.flush()
            
            # Commit para confirmar la transacción
            await self.session.commit()

            # Refrescar todos los mesas para asegurar que tengan sus datos actualizados
            for mesa in mesas:
                await self.session.refresh(mesa)

            return mesas
        except SQLAlchemyError:
            await self.session.rollback()
            raise
            

    async def get_activos(self) -> List[MesaModel]:
        """
        Obtiene todas las mesas activas.

        Returns
        -------
        List[MesaModel]
            Lista de mesas activas.
        """
        query = select(MesaModel).where(MesaModel.activo == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())