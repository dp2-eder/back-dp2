"""
Pruebas unitarias para el repositorio de opciones de pedidos.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from ulid import ULID
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.pedidos.pedido_opcion_repository import PedidoOpcionRepository
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel


@pytest.fixture
def mock_session():
    """
    Fixture que proporciona un mock de la sesión de base de datos.

    PRECONDICIONES:
        - La biblioteca unittest.mock debe estar importada correctamente.

    PROCESO:
        - Crea un mock de AsyncSession con métodos configurados.

    POSTCONDICIONES:
        - Devuelve una sesión mockeada para usar en pruebas.
    """
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def pedido_opcion_repository(mock_session):
    """
    Fixture que proporciona una instancia del repositorio con sesión mockeada.

    PRECONDICIONES:
        - El fixture mock_session debe estar disponible.

    PROCESO:
        - Crea una instancia del repositorio con la sesión mockeada.

    POSTCONDICIONES:
        - Devuelve un repositorio listo para usar en pruebas.
    """
    return PedidoOpcionRepository(mock_session)


@pytest.fixture
def sample_pedido_opcion():
    """
    Fixture que proporciona un modelo de opción de pedido de muestra.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Crea una instancia del modelo con datos de prueba.

    POSTCONDICIONES:
        - Devuelve una instancia de PedidoOpcionModel para usar en pruebas.
    """
    return PedidoOpcionModel(
        id=str(ULID()),
        id_pedido_producto=str(ULID()),
        id_producto_opcion=str(ULID()),
        precio_adicional=Decimal("5.00"),
        fecha_creacion=datetime.now(),
        creado_por=str(ULID()),
    )


@pytest.mark.asyncio
async def test_create_pedido_opcion(pedido_opcion_repository, mock_session, sample_pedido_opcion):
    """
    Prueba la creación de una opción de pedido en el repositorio.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Llama al método create con una opción de pedido de muestra.
        - Verifica que se llamen los métodos correctos de la sesión.

    POSTCONDICIONES:
        - La opción de pedido debe ser creada correctamente.
        - Los métodos add, flush, commit y refresh deben ser llamados.
    """
    # Arrange
    mock_session.add = MagicMock()

    # Act
    result = await pedido_opcion_repository.create(sample_pedido_opcion)

    # Assert
    assert result == sample_pedido_opcion
    mock_session.add.assert_called_once_with(sample_pedido_opcion)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(sample_pedido_opcion)


@pytest.mark.asyncio
async def test_get_by_id_found(pedido_opcion_repository, mock_session, sample_pedido_opcion):
    """
    Prueba la obtención de una opción de pedido por ID cuando existe.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la opción existe.
        - Llama al método get_by_id.
        - Verifica que se retorne la opción correcta.

    POSTCONDICIONES:
        - Debe retornar la opción de pedido encontrada.
    """
    # Arrange
    pedido_opcion_id = sample_pedido_opcion.id
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = sample_pedido_opcion
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await pedido_opcion_repository.get_by_id(pedido_opcion_id)

    # Assert
    assert result == sample_pedido_opcion
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_not_found(pedido_opcion_repository, mock_session):
    """
    Prueba la obtención de una opción de pedido por ID cuando no existe.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Llama al método get_by_id.
        - Verifica que se retorne None.

    POSTCONDICIONES:
        - Debe retornar None.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await pedido_opcion_repository.get_by_id(pedido_opcion_id)

    # Assert
    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_pedido_producto_id(pedido_opcion_repository, mock_session, sample_pedido_opcion):
    """
    Prueba la obtención de opciones por ID de item de pedido.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular opciones del item de pedido.
        - Llama al método get_by_pedido_producto_id.
        - Verifica que se retorne la lista correcta.

    POSTCONDICIONES:
        - Debe retornar una lista de opciones del item de pedido.
    """
    # Arrange
    pedido_producto_id = sample_pedido_opcion.id_pedido_producto
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_pedido_opcion]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await pedido_opcion_repository.get_by_pedido_producto_id(pedido_producto_id)

    # Assert
    assert result == [sample_pedido_opcion]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_success(pedido_opcion_repository, mock_session):
    """
    Prueba la eliminación exitosa de una opción de pedido.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular eliminación exitosa.
        - Llama al método delete.
        - Verifica que se retorne True.

    POSTCONDICIONES:
        - Debe retornar True y llamar a commit.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await pedido_opcion_repository.delete(pedido_opcion_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_not_found(pedido_opcion_repository, mock_session):
    """
    Prueba la eliminación cuando la opción de pedido no existe.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que no se elimina nada.
        - Llama al método delete.
        - Verifica que se retorne False.

    POSTCONDICIONES:
        - Debe retornar False.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await pedido_opcion_repository.delete(pedido_opcion_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_success(pedido_opcion_repository, mock_session, sample_pedido_opcion):
    """
    Prueba la actualización exitosa de una opción de pedido.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular actualización exitosa.
        - Llama al método update.
        - Verifica que se retorne la opción actualizada.

    POSTCONDICIONES:
        - Debe retornar la opción actualizada.
    """
    # Arrange
    pedido_opcion_id = sample_pedido_opcion.id
    update_data = {"precio_adicional": Decimal("10.00")}

    # Mock para el update
    mock_update_result = MagicMock()
    mock_update_result.rowcount = 1

    # Mock para el get_by_id posterior
    mock_get_result = MagicMock()
    mock_get_result.scalars.return_value.first.return_value = sample_pedido_opcion

    # Configurar execute para retornar diferentes resultados
    mock_session.execute = AsyncMock(side_effect=[mock_update_result, mock_get_result])

    # Act
    result = await pedido_opcion_repository.update(pedido_opcion_id, **update_data)

    # Assert
    assert result == sample_pedido_opcion
    assert mock_session.execute.call_count == 2
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_not_found(pedido_opcion_repository, mock_session):
    """
    Prueba la actualización cuando la opción de pedido no existe.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Llama al método update.
        - Verifica que se retorne None.

    POSTCONDICIONES:
        - Debe retornar None.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    update_data = {"precio_adicional": Decimal("10.00")}

    # Mock para el update
    mock_update_result = MagicMock()
    mock_update_result.rowcount = 0

    # Mock para el get_by_id posterior
    mock_get_result = MagicMock()
    mock_get_result.scalars.return_value.first.return_value = None

    mock_session.execute = AsyncMock(side_effect=[mock_update_result, mock_get_result])

    # Act
    result = await pedido_opcion_repository.update(pedido_opcion_id, **update_data)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_all(pedido_opcion_repository, mock_session, sample_pedido_opcion):
    """
    Prueba la obtención de todas las opciones de pedidos con paginación.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular resultados paginados.
        - Llama al método get_all.
        - Verifica que se retorne la tupla correcta (lista, total).

    POSTCONDICIONES:
        - Debe retornar una tupla con la lista de opciones y el total.
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_pedido_opcion]

    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1

    mock_session.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

    # Act
    result, total = await pedido_opcion_repository.get_all(skip=0, limit=10)

    # Assert
    assert result == [sample_pedido_opcion]
    assert total == 1
    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_all_with_filter(pedido_opcion_repository, mock_session, sample_pedido_opcion):
    """
    Prueba la obtención de opciones filtradas por item de pedido.

    PRECONDICIONES:
        - El repositorio y la sesión mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular resultados filtrados.
        - Llama al método get_all con filtro.
        - Verifica que se retorne la tupla correcta.

    POSTCONDICIONES:
        - Debe retornar una tupla con la lista filtrada y el total.
    """
    # Arrange
    pedido_producto_id = sample_pedido_opcion.id_pedido_producto

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_pedido_opcion]

    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1

    mock_session.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

    # Act
    result, total = await pedido_opcion_repository.get_all(
        skip=0, limit=10, id_pedido_producto=pedido_producto_id
    )

    # Assert
    assert result == [sample_pedido_opcion]
    assert total == 1
    assert mock_session.execute.call_count == 2
