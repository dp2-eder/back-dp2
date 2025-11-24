"""
Pruebas unitarias para el repositorio de tipos de opciones.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del repositorio encargado de las operaciones CRUD relacionadas con los tipos de opciones del sistema.
Se utilizan mocks para simular la capa de base de datos.

PRECONDICIONES:
    - Los módulos TipoOpcionRepository y TipoOpcionModel deben estar correctamente implementados.
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
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.pedidos.tipo_opciones_repository import TipoOpcionRepository
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente un tipo de opción por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto TipoOpcionModel cuando existe el tipo de opción.
        - El método debe retornar None cuando no existe el tipo de opción.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = TipoOpcionModel(
        id=str(ULID()), 
        codigo="nivel_aji", 
        nombre="Nivel de Ají",
        activo=True
    )
    mock_session.execute.return_value = mock_result

    tipo_opcion_id = str(ULID())
    repository = TipoOpcionRepository(mock_session)

    # Act
    result = await repository.get_by_id(tipo_opcion_id)

    # Assert
    assert result is not None
    assert isinstance(result, TipoOpcionModel)
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(tipo_opcion_id)
    assert result is None


@pytest.mark.asyncio
async def test_create_tipo_opcion():
    """
    Verifica que el método create persiste correctamente un tipo de opción en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto TipoOpcionModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de TipoOpcionModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir el tipo de opción a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar el tipo de opción creado.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    tipo_opcion = TipoOpcionModel(
        codigo="temperatura", 
        nombre="Temperatura",
        descripcion="Nivel de temperatura de la bebida",
        activo=True
    )
    repository = TipoOpcionRepository(mock_session)

    # Act
    result = await repository.create(tipo_opcion)

    # Assert - Caso exitoso
    assert result is not None
    assert result == tipo_opcion
    mock_session.add.assert_called_once_with(tipo_opcion)
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(tipo_opcion)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(tipo_opcion)



@pytest.mark.asyncio
async def test_delete_tipo_opcion():
    """
    Verifica que el método delete elimina correctamente un tipo de opción por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina un tipo de opción existente.
        - El método debe retornar False cuando no existe el tipo de opción a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina el tipo de opción)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    tipo_opcion_id = str(ULID())
    repository = TipoOpcionRepository(mock_session)

    # Act
    result = await repository.delete(tipo_opcion_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso tipo de opción no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(tipo_opcion_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(tipo_opcion_id)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_codigo():
    """
    Verifica que el método get_by_codigo recupera correctamente un tipo de opción por su código.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un código válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_codigo con un código específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto TipoOpcionModel cuando existe el tipo de opción.
        - El método debe retornar None cuando no existe el tipo de opción.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = TipoOpcionModel(
        id=str(ULID()), 
        codigo="acompanamiento", 
        nombre="Acompañamiento",
        activo=True
    )
    mock_session.execute.return_value = mock_result

    repository = TipoOpcionRepository(mock_session)

    # Act
    result = await repository.get_by_codigo("acompanamiento")

    # Assert
    assert result is not None
    assert isinstance(result, TipoOpcionModel)
    assert result.codigo == "acompanamiento"
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_codigo("codigo_inexistente")
    assert result is None


@pytest.mark.asyncio
async def test_get_activos():
    """
    Verifica que el método get_activos recupera correctamente todos los tipos de opciones activos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_activos.
        - Verificar que se ejecute la consulta correcta y se retorne la lista esperada.

    POSTCONDICIONES:
        - El método debe retornar una lista de objetos TipoOpcionModel activos.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_tipos_opciones = [
        TipoOpcionModel(id=str(ULID()), codigo="nivel_aji", nombre="Nivel de Ají", activo=True, orden=1),
        TipoOpcionModel(id=str(ULID()), codigo="temperatura", nombre="Temperatura", activo=True, orden=2),
    ]
    mock_result.scalars.return_value.all.return_value = mock_tipos_opciones
    mock_session.execute.return_value = mock_result

    repository = TipoOpcionRepository(mock_session)

    # Act
    result = await repository.get_activos()

    # Assert
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(tipo_opcion, TipoOpcionModel) for tipo_opcion in result)
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_all():
    """
    Verifica que el método get_all recupera correctamente una lista paginada de tipos de opciones.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular las respuestas de la base de datos.
        - Llamar al método get_all con parámetros de paginación.
        - Verificar que se ejecuten las consultas correctas y se retorne la tupla esperada.

    POSTCONDICIONES:
        - El método debe retornar una tupla con lista de tipos de opciones y total de registros.
        - Las consultas SQL deben formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mock para la consulta de tipos de opciones
    mock_result = MagicMock()
    mock_tipos_opciones = [
        TipoOpcionModel(id=str(ULID()), codigo="nivel_aji", nombre="Nivel de Ají"),
        TipoOpcionModel(id=str(ULID()), codigo="temperatura", nombre="Temperatura"),
    ]
    mock_result.scalars.return_value.all.return_value = mock_tipos_opciones
    
    # Mock para la consulta de conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2
    
    # Configurar el mock para devolver diferentes resultados según la consulta
    def mock_execute_side_effect(query):
        if "count" in str(query):
            return mock_count_result
        return mock_result
    
    mock_session.execute.side_effect = mock_execute_side_effect

    repository = TipoOpcionRepository(mock_session)

    # Act
    result = await repository.get_all(skip=0, limit=10)

    # Assert
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    tipos_opciones, total = result
    assert isinstance(tipos_opciones, list)
    assert len(tipos_opciones) == 2
    assert total == 2
    assert all(isinstance(tipo_opcion, TipoOpcionModel) for tipo_opcion in tipos_opciones)
    
    # Verificar que se llamó execute dos veces (una para datos, otra para conteo)
    assert mock_session.execute.call_count == 2

