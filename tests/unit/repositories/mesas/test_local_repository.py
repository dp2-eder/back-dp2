"""
Pruebas unitarias para el repositorio de locales.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del repositorio encargado de las operaciones CRUD relacionadas con los locales del sistema.
Se utilizan mocks para simular la capa de base de datos.

PRECONDICIONES:
    - Los módulos LocalRepository y LocalModel deben estar correctamente implementados.
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
from ulid import ULID
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.local_model import LocalModel
from src.core.enums.local_enums import TipoLocal


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente un local por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto LocalModel cuando existe el local.
        - El método debe retornar None cuando no existe el local.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = LocalModel(
        id=str(ULID()),
        codigo="CEV-001",
        nombre="La Cevichería del Centro",
        direccion="Av. Principal 123",
        tipo_local=TipoLocal.CENTRAL,
    )
    mock_session.execute.return_value = mock_result

    local_id = str(ULID())
    repository = LocalRepository(mock_session)

    # Act
    result = await repository.get_by_id(local_id)

    # Assert
    assert result is not None
    assert isinstance(result, LocalModel)
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(local_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_codigo():
    """
    Verifica que el método get_by_codigo recupera correctamente un local por su código.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un código válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_codigo con un código específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto LocalModel cuando existe el local.
        - El método debe retornar None cuando no existe el local.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    codigo = "CEV-001"
    mock_result.scalars.return_value.first.return_value = LocalModel(
        id=str(ULID()),
        codigo=codigo,
        nombre="La Cevichería del Centro",
        direccion="Av. Principal 123",
        tipo_local=TipoLocal.CENTRAL,
    )
    mock_session.execute.return_value = mock_result

    repository = LocalRepository(mock_session)

    # Act
    result = await repository.get_by_codigo(codigo)

    # Assert
    assert result is not None
    assert isinstance(result, LocalModel)
    assert result.codigo == codigo
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_codigo("CEV-999")
    assert result is None


@pytest.mark.asyncio
async def test_create_local():
    """
    Verifica que el método create persiste correctamente un local en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto LocalModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de LocalModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir el local a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar el local creado.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    local = LocalModel(
        codigo="CEV-002",
        nombre="La Cevichería de Miraflores",
        direccion="Calle Los Olivos 456",
        distrito="Miraflores",
        ciudad="Lima",
        tipo_local=TipoLocal.SUCURSAL,
        capacidad_total=80,
        fecha_apertura=date(2024, 1, 15),
    )
    repository = LocalRepository(mock_session)

    # Act
    result = await repository.create(local)

    # Assert - Caso exitoso
    assert result is not None
    assert result == local
    mock_session.add.assert_called_once_with(local)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(local)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(local)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_local():
    """
    Verifica que el método delete elimina correctamente un local por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina un local existente.
        - El método debe retornar False cuando no existe el local a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina el local)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    local_id = str(ULID())
    repository = LocalRepository(mock_session)

    # Act
    result = await repository.delete(local_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso local no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(local_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(local_id)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_local():
    """
    Verifica que el método update actualiza correctamente un local.
    """
    # Arrange - Caso exitoso
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result

    local_id = str(ULID())
    updated_local = LocalModel(
        id=local_id,
        codigo="CEV-003",
        nombre="Local Actualizado",
        direccion="Nueva Dirección 789",
        tipo_local=TipoLocal.CENTRAL,
    )

    # Mock para get_by_id que se llama después del update
    async def mock_get_by_id(local_id):
        return updated_local if local_id == updated_local.id else None

    repository = LocalRepository(mock_session)
    repository.get_by_id = mock_get_by_id

    # Act
    result = await repository.update(local_id, nombre="Local Actualizado")

    # Assert
    assert result is not None
    assert result.nombre == "Local Actualizado"
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_all():
    """
    Verifica que el método get_all retorna una lista paginada de locales.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular múltiples locales en la base de datos.
        - Llamar al método get_all con parámetros de paginación.
        - Verificar que se retorne la lista correcta y el total de registros.

    POSTCONDICIONES:
        - El método debe retornar una tupla con la lista de locales y el total.
        - La paginación debe funcionar correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock para la consulta de locales
    mock_result = MagicMock()
    locales = [
        LocalModel(
            id=str(ULID()),
            codigo="CEV-001",
            nombre="Local 1",
            direccion="Dirección 1",
            tipo_local=TipoLocal.CENTRAL,
        ),
        LocalModel(
            id=str(ULID()),
            codigo="CEV-002",
            nombre="Local 2",
            direccion="Dirección 2",
            tipo_local=TipoLocal.SUCURSAL,
        ),
    ]
    mock_result.scalars.return_value.all.return_value = locales

    # Mock para la consulta de conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    # Configurar el mock para retornar diferentes resultados
    mock_session.execute.side_effect = [mock_result, mock_count_result]

    repository = LocalRepository(mock_session)

    # Act
    result_locales, total = await repository.get_all(skip=0, limit=10)

    # Assert
    assert len(result_locales) == 2
    assert total == 2
    assert result_locales[0].codigo == "CEV-001"
    assert result_locales[1].codigo == "CEV-002"
    assert mock_session.execute.call_count == 2
