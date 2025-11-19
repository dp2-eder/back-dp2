"""
Servicio para la gestión de divisiones de cuenta en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from typing import List

from src.repositories.pagos.division_cuenta_repository import DivisionCuentaRepository
from src.repositories.pagos.division_cuenta_detalle_repository import DivisionCuentaDetalleRepository
from src.repositories.pedidos.pedido_repository import PedidoRepository
from src.models.pagos.division_cuenta_model import DivisionCuentaModel
from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel
from src.api.schemas.division_cuenta_schema import (
    DivisionCuentaCreate,
    DivisionCuentaUpdate,
    DivisionCuentaResponse,
    DivisionCuentaSummary,
    DivisionCuentaList,
)
from src.business_logic.exceptions.division_cuenta_exceptions import (
    DivisionCuentaValidationError,
    DivisionCuentaNotFoundError,
    DivisionCuentaConflictError,
)


class DivisionCuentaService:
    """Servicio para la gestión de divisiones de cuenta en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con divisiones de cuenta, incluyendo validaciones y cálculos.

    Attributes
    ----------
    repository : DivisionCuentaRepository
        Repositorio para acceso a datos de divisiones de cuenta.
    detalle_repository : DivisionCuentaDetalleRepository
        Repositorio para acceso a datos de detalles.
    pedido_repository : PedidoRepository
        Repositorio para validar la existencia de pedidos.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = DivisionCuentaRepository(session)
        self.detalle_repository = DivisionCuentaDetalleRepository(session)
        self.pedido_repository = PedidoRepository(session)
        self.session = session

    async def create_division(self, division_data: DivisionCuentaCreate) -> DivisionCuentaResponse:
        """
        Crea una nueva división de cuenta.

        Parameters
        ----------
        division_data : DivisionCuentaCreate
            Datos para crear la nueva división.

        Returns
        -------
        DivisionCuentaResponse
            Esquema de respuesta con los datos de la división creada.

        Raises
        ------
        DivisionCuentaValidationError
            Si los datos no cumplen con las validaciones o el pedido no existe.
        DivisionCuentaConflictError
            Si hay un conflicto al crear la división.
        """
        # Validar que cantidad_personas > 0
        if division_data.cantidad_personas < 1:
            raise DivisionCuentaValidationError(
                "La cantidad de personas debe ser mayor a 0"
            )

        # Validar que el pedido existe
        pedido = await self.pedido_repository.get_by_id(division_data.id_pedido)
        if not pedido:
            raise DivisionCuentaValidationError(
                f"El pedido con ID '{division_data.id_pedido}' no existe"
            )

        try:
            # Crear modelo de división
            division = DivisionCuentaModel(
                id_pedido=division_data.id_pedido,
                tipo_division=division_data.tipo_division,
                cantidad_personas=division_data.cantidad_personas,
                notas=division_data.notas,
            )

            # Persistir en la base de datos
            created_division = await self.repository.create(division)

            # Convertir y retornar como esquema de respuesta
            return DivisionCuentaResponse.model_validate(created_division)
        except IntegrityError as e:
            raise DivisionCuentaConflictError(f"Error al crear la división: {str(e)}")

    async def calcular_division_equitativa(
        self, division_id: str
    ) -> DivisionCuentaResponse:
        """
        Calcula y crea detalles para división equitativa.

        Divide el total del pedido equitativamente entre todas las personas.

        Parameters
        ----------
        division_id : str
            ID de la división de cuenta.

        Returns
        -------
        DivisionCuentaResponse
            División con detalles calculados.

        Raises
        ------
        DivisionCuentaNotFoundError
            Si no se encuentra la división.
        DivisionCuentaValidationError
            Si el pedido no tiene productos o el tipo no es equitativa.
        """
        # Obtener división con detalles y pedido
        division = await self.repository.get_with_detalles(division_id)
        if not division:
            raise DivisionCuentaNotFoundError(
                f"No se encontró la división con ID {division_id}"
            )

        # Validar tipo de división
        if division.tipo_division.value != "equitativa":
            raise DivisionCuentaValidationError(
                "Este método solo aplica para divisiones equitativas"
            )

        # Obtener pedido completo
        pedido = await self.pedido_repository.get_by_id(division.id_pedido)
        if not pedido:
            raise DivisionCuentaValidationError("El pedido asociado no existe")

        # Calcular monto por persona
        total_pedido = pedido.total
        monto_por_persona = total_pedido / Decimal(division.cantidad_personas)

        # Limpiar detalles existentes si los hay
        for detalle in division.detalles:
            await self.detalle_repository.delete(detalle.id)

        # Crear un detalle por persona indicando su monto
        # (En una división equitativa, cada persona paga igual sin importar qué comió)
        # Esto se puede representar como un único detalle por persona
        # TODO: Implementar lógica específica según modelo de negocio
        # Por ahora, solo calculamos el monto

        await self.session.flush()
        await self.session.refresh(division)

        return DivisionCuentaResponse.model_validate(division)

    async def get_division_by_id(self, division_id: str) -> DivisionCuentaResponse:
        """
        Obtiene una división por su ID.

        Parameters
        ----------
        division_id : str
            Identificador único de la división (ULID).

        Returns
        -------
        DivisionCuentaResponse
            Esquema de respuesta con los datos de la división.

        Raises
        ------
        DivisionCuentaNotFoundError
            Si no se encuentra una división con el ID proporcionado.
        """
        division = await self.repository.get_by_id(division_id)

        if not division:
            raise DivisionCuentaNotFoundError(
                f"No se encontró la división con ID {division_id}"
            )

        return DivisionCuentaResponse.model_validate(division)

    async def get_divisiones_by_pedido(self, pedido_id: str) -> List[DivisionCuentaResponse]:
        """
        Obtiene divisiones por pedido.

        Parameters
        ----------
        pedido_id : str
            ID del pedido.

        Returns
        -------
        List[DivisionCuentaResponse]
            Lista de divisiones del pedido.
        """
        divisiones = await self.repository.get_by_pedido(pedido_id)
        return [DivisionCuentaResponse.model_validate(d) for d in divisiones]

    async def get_divisiones(self, skip: int = 0, limit: int = 100) -> DivisionCuentaList:
        """
        Obtiene una lista paginada de divisiones.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        DivisionCuentaList
            Esquema con la lista de divisiones y el total.
        """
        if skip < 0:
            raise DivisionCuentaValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise DivisionCuentaValidationError(
                "El parámetro 'limit' debe ser mayor a cero"
            )

        divisiones, total = await self.repository.get_all(skip, limit)
        division_summaries = [DivisionCuentaSummary.model_validate(d) for d in divisiones]

        return DivisionCuentaList(items=division_summaries, total=total)

    async def update_division(
        self, division_id: str, division_data: DivisionCuentaUpdate
    ) -> DivisionCuentaResponse:
        """
        Actualiza una división existente.

        Parameters
        ----------
        division_id : str
            Identificador único de la división (ULID).
        division_data : DivisionCuentaUpdate
            Datos para actualizar la división.

        Returns
        -------
        DivisionCuentaResponse
            Esquema de respuesta con los datos actualizados.

        Raises
        ------
        DivisionCuentaNotFoundError
            Si no se encuentra la división.
        DivisionCuentaValidationError
            Si los datos no son válidos.
        DivisionCuentaConflictError
            Si hay un conflicto al actualizar.
        """
        update_data = division_data.model_dump(exclude_none=True)

        if not update_data:
            return await self.get_division_by_id(division_id)

        # Validar cantidad_personas si se proporciona
        if "cantidad_personas" in update_data and update_data["cantidad_personas"] < 1:
            raise DivisionCuentaValidationError(
                "La cantidad de personas debe ser mayor a 0"
            )

        try:
            updated_division = await self.repository.update(division_id, **update_data)

            if not updated_division:
                raise DivisionCuentaNotFoundError(
                    f"No se encontró la división con ID {division_id}"
                )

            return DivisionCuentaResponse.model_validate(updated_division)
        except IntegrityError as e:
            raise DivisionCuentaConflictError(f"Error al actualizar la división: {str(e)}")

    async def delete_division(self, division_id: str) -> bool:
        """
        Elimina una división por su ID.

        Parameters
        ----------
        division_id : str
            Identificador único de la división (ULID).

        Returns
        -------
        bool
            True si la división fue eliminada correctamente.

        Raises
        ------
        DivisionCuentaNotFoundError
            Si no se encuentra la división.
        """
        division = await self.repository.get_by_id(division_id)
        if not division:
            raise DivisionCuentaNotFoundError(
                f"No se encontró la división con ID {division_id}"
            )

        result = await self.repository.delete(division_id)
        return result
