"""
Pruebas unitarias para el repositorio de items de pedidos (pedido_producto).
"""

import pytest
from decimal import Decimal
from ulid import ULID
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.pedidos.pedido_producto_repository import PedidoProductoRepository
from src.models.pedidos.pedido_producto_model import PedidoProductoModel


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente un item por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto PedidoProductoModel cuando existe el item.
        - El método debe retornar None cuando no existe el item.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = PedidoProductoModel(
        id=str(ULID()),
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=2,
        precio_unitario=Decimal("50.00"),
        precio_opciones=Decimal("5.00"),
        subtotal=Decimal("110.00"),
    )
    mock_session.execute.return_value = mock_result

    item_id = str(ULID())
    repository = PedidoProductoRepository(mock_session)

    # Act
    result = await repository.get_by_id(item_id)

    # Assert
    assert result is not None
    assert isinstance(result, PedidoProductoModel)
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(item_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_pedido_id():
    """
    Verifica que el método get_by_pedido_id recupera todos los items de un pedido.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un pedido_id válido.

    PROCESO:
        - Configurar el mock para simular múltiples items de un pedido.
        - Llamar al método get_by_pedido_id.
        - Verificar que se retorne una lista de items.

    POSTCONDICIONES:
        - El método debe retornar una lista de PedidoProductoModel.
        - Los items deben pertenecer al pedido especificado.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    pedido_id = str(ULID())
    items = [
        PedidoProductoModel(
            id=str(ULID()),
            id_pedido=pedido_id,
            id_producto=str(ULID()),
            cantidad=1,
            precio_unitario=Decimal("30.00"),
            precio_opciones=Decimal("0.00"),
            subtotal=Decimal("30.00"),
        ),
        PedidoProductoModel(
            id=str(ULID()),
            id_pedido=pedido_id,
            id_producto=str(ULID()),
            cantidad=2,
            precio_unitario=Decimal("25.00"),
            precio_opciones=Decimal("5.00"),
            subtotal=Decimal("60.00"),
        ),
    ]
    mock_result.scalars.return_value.all.return_value = items
    mock_session.execute.return_value = mock_result

    repository = PedidoProductoRepository(mock_session)

    # Act
    result = await repository.get_by_pedido_id(pedido_id)

    # Assert
    assert len(result) == 2
    assert all(isinstance(item, PedidoProductoModel) for item in result)
    assert all(item.id_pedido == pedido_id for item in result)
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_pedido_producto():
    """
    Verifica que el método create persiste correctamente un item de pedido.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto PedidoProductoModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de PedidoProductoModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir el item a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar el item creado.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    item = PedidoProductoModel(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=3,
        precio_unitario=Decimal("15.00"),
        precio_opciones=Decimal("2.00"),
        subtotal=Decimal("51.00"),
    )
    repository = PedidoProductoRepository(mock_session)

    # Act
    result = await repository.create(item)

    # Assert - Caso exitoso
    assert result is not None
    assert result == item
    mock_session.add.assert_called_once_with(item)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(item)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(item)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_pedido_producto():
    """
    Verifica que el método delete elimina correctamente un item por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina un item existente.
        - El método debe retornar False cuando no existe el item a eliminar.
    """
    # Arrange - Caso exitoso (se elimina el item)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    item_id = str(ULID())
    repository = PedidoProductoRepository(mock_session)

    # Act
    result = await repository.delete(item_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso item no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(item_id)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_update_pedido_producto():
    """
    Verifica que el método update actualiza correctamente un item.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido y campos para actualizar.

    PROCESO:
        - Configurar los mocks para simular la actualización y consulta.
        - Llamar al método update con ID y campos a actualizar.
        - Verificar que se ejecute la actualización y se retorne el item actualizado.

    POSTCONDICIONES:
        - El método debe actualizar los campos especificados.
        - El método debe retornar el item actualizado.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    item_id = str(ULID())

    # Mock del execute para el update
    mock_update_result = MagicMock()
    mock_update_result.rowcount = 1

    # Mock del get_by_id para retornar el item actualizado
    updated_item = PedidoProductoModel(
        id=item_id,
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=5,
        precio_unitario=Decimal("20.00"),
        precio_opciones=Decimal("3.00"),
        subtotal=Decimal("115.00"),
    )

    repository = PedidoProductoRepository(mock_session)
    repository.get_by_id = AsyncMock(return_value=updated_item)

    mock_session.execute.return_value = mock_update_result

    # Act
    result = await repository.update(item_id, cantidad=5, subtotal=Decimal("115.00"))

    # Assert
    assert result is not None
    assert result.cantidad == 5
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    repository.get_by_id.assert_called_once_with(item_id)


@pytest.mark.asyncio
async def test_get_all_with_filters():
    """
    Verifica que el método get_all obtiene items con filtros correctamente.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular resultados paginados y conteo.
        - Llamar al método get_all con filtros.
        - Verificar que se retornen los items y el total correctamente.

    POSTCONDICIONES:
        - El método debe retornar una tupla (lista, total).
        - Los filtros deben aplicarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    pedido_id = str(ULID())

    # Mock para la consulta de items
    mock_result = MagicMock()
    items = [
        PedidoProductoModel(
            id=str(ULID()),
            id_pedido=pedido_id,
            id_producto=str(ULID()),
            cantidad=1,
            precio_unitario=Decimal("30.00"),
            precio_opciones=Decimal("0.00"),
            subtotal=Decimal("30.00"),
        ),
        PedidoProductoModel(
            id=str(ULID()),
            id_pedido=pedido_id,
            id_producto=str(ULID()),
            cantidad=2,
            precio_unitario=Decimal("25.00"),
            precio_opciones=Decimal("5.00"),
            subtotal=Decimal("60.00"),
        ),
    ]
    mock_result.scalars.return_value.all.return_value = items

    # Mock para el count
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    mock_session.execute.side_effect = [mock_result, mock_count_result]

    repository = PedidoProductoRepository(mock_session)

    # Act
    result_items, total = await repository.get_all(skip=0, limit=10, id_pedido=pedido_id)

    # Assert
    assert len(result_items) == 2
    assert total == 2
    assert all(isinstance(item, PedidoProductoModel) for item in result_items)
    assert all(item.id_pedido == pedido_id for item in result_items)
    assert mock_session.execute.call_count == 2
