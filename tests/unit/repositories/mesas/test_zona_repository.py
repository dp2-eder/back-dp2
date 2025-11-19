"""
Pruebas unitarias para el repositorio de zonas.
"""

import pytest
from ulid import ULID
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.mesas.zona_repository import ZonaRepository
from src.models.mesas.zona_model import ZonaModel


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente una zona por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto ZonaModel cuando existe la zona.
        - El método debe retornar None cuando no existe la zona.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    local_id = str(ULID())
    mock_result.scalars.return_value.first.return_value = ZonaModel(
        id=str(ULID()),
        id_local=local_id,
        nombre="Terraza",
        nivel=0,
    )
    mock_session.execute.return_value = mock_result

    zona_id = str(ULID())
    repository = ZonaRepository(mock_session)

    # Act
    result = await repository.get_by_id(zona_id)

    # Assert
    assert result is not None
    assert isinstance(result, ZonaModel)
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(zona_id)
    assert result is None


@pytest.mark.asyncio
async def test_create_zona():
    """
    Verifica que el método create persiste correctamente una zona en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto ZonaModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de ZonaModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir la zona a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar la zona creada.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    local_id = str(ULID())
    zona = ZonaModel(
        id_local=local_id,
        nombre="Interior",
        descripcion="Zona interior principal",
        nivel=0,
        capacidad_maxima=60,
    )
    repository = ZonaRepository(mock_session)

    # Act
    result = await repository.create(zona)

    # Assert - Caso exitoso
    assert result is not None
    assert result == zona
    mock_session.add.assert_called_once_with(zona)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(zona)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(zona)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_zona():
    """
    Verifica que el método delete elimina correctamente una zona por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina una zona existente.
        - El método debe retornar False cuando no existe la zona a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina la zona)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    zona_id = str(ULID())
    repository = ZonaRepository(mock_session)

    # Act
    result = await repository.delete(zona_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso zona no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(zona_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(zona_id)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_zona():
    """
    Verifica que el método update actualiza correctamente una zona.
    """
    # Arrange - Caso exitoso
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result

    zona_id = str(ULID())
    local_id = str(ULID())
    updated_zona = ZonaModel(
        id=zona_id,
        id_local=local_id,
        nombre="Zona Actualizada",
        nivel=0,
    )

    # Mock para get_by_id que se llama después del update
    async def mock_get_by_id(zona_id):
        return updated_zona if zona_id == updated_zona.id else None

    repository = ZonaRepository(mock_session)
    repository.get_by_id = mock_get_by_id

    # Act
    result = await repository.update(zona_id, nombre="Zona Actualizada")

    # Assert
    assert result is not None
    assert result.nombre == "Zona Actualizada"
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_all():
    """
    Verifica que el método get_all retorna una lista paginada de zonas.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular múltiples zonas en la base de datos.
        - Llamar al método get_all con parámetros de paginación.
        - Verificar que se retorne la lista correcta y el total de registros.

    POSTCONDICIONES:
        - El método debe retornar una tupla con la lista de zonas y el total.
        - La paginación debe funcionar correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    local_id = str(ULID())

    # Mock para la consulta de zonas
    mock_result = MagicMock()
    zonas = [
        ZonaModel(
            id=str(ULID()),
            id_local=local_id,
            nombre="Terraza",
            nivel=0,
        ),
        ZonaModel(
            id=str(ULID()),
            id_local=local_id,
            nombre="Interior",
            nivel=0,
        ),
    ]
    mock_result.scalars.return_value.all.return_value = zonas

    # Mock para la consulta de conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    # Configurar el mock para retornar diferentes resultados
    mock_session.execute.side_effect = [mock_result, mock_count_result]

    repository = ZonaRepository(mock_session)

    # Act
    result_zonas, total = await repository.get_all(skip=0, limit=10)

    # Assert
    assert len(result_zonas) == 2
    assert total == 2
    assert result_zonas[0].nombre == "Terraza"
    assert result_zonas[1].nombre == "Interior"
    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_by_local():
    """
    Verifica que el método get_by_local retorna zonas filtradas por local.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un local_id válido.

    PROCESO:
        - Configurar los mocks para simular zonas de un local específico.
        - Llamar al método get_by_local con un local_id.
        - Verificar que se retorne la lista correcta.

    POSTCONDICIONES:
        - El método debe retornar zonas del local especificado.
        - El total debe coincidir con el número de zonas.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    local_id = str(ULID())

    # Mock para la consulta de zonas
    mock_result = MagicMock()
    zonas = [
        ZonaModel(id=str(ULID()), id_local=local_id, nombre="Zona 1", nivel=0),
        ZonaModel(id=str(ULID()), id_local=local_id, nombre="Zona 2", nivel=1),
    ]
    mock_result.scalars.return_value.all.return_value = zonas

    # Mock para la consulta de conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    mock_session.execute.side_effect = [mock_result, mock_count_result]
    repository = ZonaRepository(mock_session)

    # Act
    result_zonas, total = await repository.get_by_local(local_id, skip=0, limit=10)

    # Assert
    assert len(result_zonas) == 2
    assert total == 2
    assert all(z.id_local == local_id for z in result_zonas)


@pytest.mark.asyncio
async def test_get_by_nivel():
    """
    Verifica que el método get_by_nivel retorna zonas filtradas por nivel.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular zonas de un nivel específico.
        - Llamar al método get_by_nivel con un nivel.
        - Verificar que se retorne la lista correcta.

    POSTCONDICIONES:
        - El método debe retornar zonas del nivel especificado.
        - El total debe coincidir con el número de zonas.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    local_id = str(ULID())
    nivel = 0

    # Mock para la consulta de zonas
    mock_result = MagicMock()
    zonas = [
        ZonaModel(id=str(ULID()), id_local=local_id, nombre="Zona Principal 1", nivel=0),
        ZonaModel(id=str(ULID()), id_local=local_id, nombre="Zona Principal 2", nivel=0),
    ]
    mock_result.scalars.return_value.all.return_value = zonas

    # Mock para la consulta de conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    mock_session.execute.side_effect = [mock_result, mock_count_result]
    repository = ZonaRepository(mock_session)

    # Act
    result_zonas, total = await repository.get_by_nivel(nivel, skip=0, limit=10)

    # Assert
    assert len(result_zonas) == 2
    assert total == 2
    assert all(z.nivel == nivel for z in result_zonas)
