"""
Pruebas unitarias para el repositorio de pedidos.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del repositorio encargado de las operaciones CRUD relacionadas con los pedidos del sistema.
Se utilizan mocks para simular la capa de base de datos.

PRECONDICIONES:
    - Los módulos PedidoRepository y PedidoModel deben estar correctamente implementados.
    - SQLAlchemy y sus dependencias deben estar instaladas.
    - pytest y pytest-asyncio deben estar disponibles para ejecutar pruebas asíncronas.

PROCESO:
    - Configurar mocks para simular la sesión de base de datos.
    - Ejecutar los métodos del repositorio con parámetros controlados.
    - Verificar que el comportamiento de los métodos sea el esperado.

POSTCONDICIONES:
    - Todas las pruebas deben pasar satisfactoriamente.
    - Los métodos del repositorio deben funcionar según las especificaciones.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from ulid import ULID
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.pedidos.pedido_repository import PedidoRepository
from src.models.pedidos.pedido_model import PedidoModel
from src.core.enums.pedido_enums import EstadoPedido


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente un pedido por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto PedidoModel cuando existe el pedido.
        - El método debe retornar None cuando no existe el pedido.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = PedidoModel(
        id=str(ULID()),
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
        estado=EstadoPedido.PENDIENTE,
        total=Decimal("100.00"),
    )
    mock_session.execute.return_value = mock_result

    pedido_id = str(ULID())
    repository = PedidoRepository(mock_session)

    # Act
    result = await repository.get_by_id(pedido_id)

    # Assert
    assert result is not None
    assert isinstance(result, PedidoModel)
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(pedido_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_numero_pedido():
    """
    Verifica que el método get_by_numero_pedido recupera correctamente un pedido por su número.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un numero_pedido válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_numero_pedido con un número específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto PedidoModel cuando existe el pedido.
        - El método debe retornar None cuando no existe el pedido.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    numero_pedido = "20251026-M001-001"
    mock_result.scalars.return_value.first.return_value = PedidoModel(
        id=str(ULID()),
        id_mesa=str(ULID()),
        numero_pedido=numero_pedido,
        estado=EstadoPedido.PENDIENTE,
        total=Decimal("100.00"),
    )
    mock_session.execute.return_value = mock_result

    repository = PedidoRepository(mock_session)

    # Act
    result = await repository.get_by_numero_pedido(numero_pedido)

    # Assert
    assert result is not None
    assert isinstance(result, PedidoModel)
    assert result.numero_pedido == numero_pedido
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_pedido():
    """
    Verifica que el método create persiste correctamente un pedido en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto PedidoModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de PedidoModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir el pedido a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar el pedido creado.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    pedido = PedidoModel(
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
        estado=EstadoPedido.PENDIENTE,
        total=Decimal("100.00"),
    )
    repository = PedidoRepository(mock_session)

    # Act
    result = await repository.create(pedido)

    # Assert - Caso exitoso
    assert result is not None
    assert result == pedido
    mock_session.add.assert_called_once_with(pedido)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(pedido)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(pedido)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_pedido():
    """
    Verifica que el método delete elimina correctamente un pedido por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina un pedido existente.
        - El método debe retornar False cuando no existe el pedido a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina el pedido)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    pedido_id = str(ULID())
    repository = PedidoRepository(mock_session)

    # Act
    result = await repository.delete(pedido_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso pedido no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(pedido_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(pedido_id)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_pedido():
    """
    Verifica que el método update actualiza correctamente un pedido.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido y campos para actualizar.

    PROCESO:
        - Configurar los mocks para simular la actualización y consulta.
        - Llamar al método update con ID y campos a actualizar.
        - Verificar que se ejecute la actualización y se retorne el pedido actualizado.

    POSTCONDICIONES:
        - El método debe actualizar los campos especificados.
        - El método debe retornar el pedido actualizado.
        - El método debe retornar None si el pedido no existe.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    pedido_id = str(ULID())

    # Mock del execute para el update
    mock_update_result = MagicMock()
    mock_update_result.rowcount = 1

    # Mock del get_by_id para retornar el pedido actualizado
    updated_pedido = PedidoModel(
        id=pedido_id,
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
        estado=EstadoPedido.CONFIRMADO,
        total=Decimal("150.00"),
    )

    repository = PedidoRepository(mock_session)
    repository.get_by_id = AsyncMock(return_value=updated_pedido)

    mock_session.execute.return_value = mock_update_result

    # Act
    result = await repository.update(pedido_id, estado=EstadoPedido.CONFIRMADO)

    # Assert
    assert result is not None
    assert result.estado == EstadoPedido.CONFIRMADO
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    repository.get_by_id.assert_called_once_with(pedido_id)


@pytest.mark.asyncio
async def test_get_all_with_filters():
    """
    Verifica que el método get_all obtiene pedidos con filtros correctamente.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular resultados paginados y conteo.
        - Llamar al método get_all con filtros.
        - Verificar que se retornen los pedidos y el total correctamente.

    POSTCONDICIONES:
        - El método debe retornar una tupla (lista, total).
        - Los filtros deben aplicarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock para la consulta de pedidos
    mock_result = MagicMock()
    pedidos = [
        PedidoModel(
            id=str(ULID()),
            id_mesa=str(ULID()),
            numero_pedido="20251026-M001-001",
            estado=EstadoPedido.PENDIENTE,
            total=Decimal("100.00"),
        ),
        PedidoModel(
            id=str(ULID()),
            id_mesa=str(ULID()),
            numero_pedido="20251026-M001-002",
            estado=EstadoPedido.PENDIENTE,
            total=Decimal("150.00"),
        ),
    ]
    mock_result.scalars.return_value.all.return_value = pedidos

    # Mock para el count
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    mock_session.execute.side_effect = [mock_result, mock_count_result]

    repository = PedidoRepository(mock_session)

    # Act
    result_pedidos, total = await repository.get_all(
        skip=0, limit=10, estado=EstadoPedido.PENDIENTE
    )

    # Assert
    assert len(result_pedidos) == 2
    assert total == 2
    assert all(isinstance(p, PedidoModel) for p in result_pedidos)
    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_last_sequence_for_date_and_mesa():
    """
    Verifica que el método get_last_sequence_for_date_and_mesa obtiene la última secuencia correctamente.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener una fecha y número de mesa.

    PROCESO:
        - Configurar el mock para simular el último numero_pedido.
        - Llamar al método con fecha y mesa.
        - Verificar que se extraiga la secuencia correctamente.

    POSTCONDICIONES:
        - El método debe retornar la secuencia del último pedido.
        - El método debe retornar 0 si no hay pedidos.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()

    # Simular último numero_pedido: "20251026-M001-005"
    mock_result.scalar.return_value = "20251026-M001-005"
    mock_session.execute.return_value = mock_result

    repository = PedidoRepository(mock_session)

    # Act
    date = datetime(2025, 10, 26)
    last_seq = await repository.get_last_sequence_for_date_and_mesa(date, "001")

    # Assert
    assert last_seq == 5
    mock_session.execute.assert_called_once()

    # Caso sin pedidos previos
    mock_session.reset_mock()
    mock_result.scalar.return_value = None

    last_seq = await repository.get_last_sequence_for_date_and_mesa(date, "001")
    assert last_seq == 0
