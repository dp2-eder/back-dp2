"""
Pruebas unitarias para el repositorio de categorías.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del repositorio encargado de las operaciones CRUD relacionadas con las categorías del sistema.
Se utilizan mocks para simular la capa de base de datos.

PRECONDICIONES:
    - Los módulos CategoriaRepository y CategoriaModel deben estar correctamente implementados.
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
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.menu.categoria_repository import CategoriaRepository
from src.models.menu.categoria_model import CategoriaModel


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente una categoría por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto CategoriaModel cuando existe la categoría.
        - El método debe retornar None cuando no existe la categoría.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = CategoriaModel(
        id=str(ULID()), nombre="Entradas", descripcion="Platos de entrada"
    )
    mock_session.execute.return_value = mock_result

    categoria_id = str(ULID())
    repository = CategoriaRepository(mock_session)

    # Act
    result = await repository.get_by_id(categoria_id)

    # Assert
    assert result is not None
    assert isinstance(result, CategoriaModel)
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(categoria_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_nombre():
    """
    Verifica que el método get_by_nombre recupera correctamente una categoría por su nombre.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un nombre válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_nombre con un nombre específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto CategoriaModel cuando existe la categoría.
        - El método debe retornar None cuando no existe la categoría.
        - La consulta SQL debe formarse correctamente.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = CategoriaModel(
        id=str(ULID()), nombre="Bebidas", descripcion="Bebidas y refrescos"
    )
    mock_session.execute.return_value = mock_result

    nombre = "Bebidas"
    repository = CategoriaRepository(mock_session)

    # Act
    result = await repository.get_by_nombre(nombre)

    # Assert
    assert result is not None
    assert isinstance(result, CategoriaModel)
    assert result.nombre == nombre
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_nombre("No existe")
    assert result is None


@pytest.mark.asyncio
async def test_create_categoria():
    """
    Verifica que el método create persiste correctamente una categoría en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto CategoriaModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de CategoriaModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir la categoría a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar la categoría creada.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    categoria = CategoriaModel(nombre="Postres", descripcion="Dulces y postres")
    repository = CategoriaRepository(mock_session)

    # Act
    result = await repository.create(categoria)

    # Assert - Caso exitoso
    assert result is not None
    assert result == categoria
    mock_session.add.assert_called_once_with(categoria)
    mock_session.flush.assert_called_once()
    # mock_session.commit.assert_called_once()  # BaseRepository no hace commit
    mock_session.refresh.assert_called_once_with(categoria)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(categoria)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_categoria():
    """
    Verifica que el método delete elimina correctamente una categoría por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina una categoría existente.
        - El método debe retornar False cuando no existe la categoría a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina la categoría)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    categoria_id = str(ULID())
    repository = CategoriaRepository(mock_session)

    # Act
    result = await repository.delete(categoria_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    # mock_session.commit.assert_called_once() # BaseRepository no hace commit

    # Arrange - Caso categoría no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(categoria_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    # mock_session.commit.assert_called_once() # BaseRepository no hace commit

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(categoria_id)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_categoria():
    """
    Verifica que el método update actualiza correctamente una categoría existente.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido y datos para actualizar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método update con un ID y datos de actualización.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar la categoría actualizada cuando existe.
        - El método debe retornar None cuando no existe la categoría.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    existing_categoria = CategoriaModel(
        id=str(ULID()), nombre="Original", descripcion="Original desc"
    )
    # Mock get_by_id response
    mock_result.scalars.return_value.first.return_value = existing_categoria
    mock_session.execute.return_value = mock_result

    categoria_id = str(ULID())
    repository = CategoriaRepository(mock_session)

    # Act
    result = await repository.update(
        categoria_id, nombre="Actualizado", descripcion="Nueva descripción"
    )

    # Assert
    assert result is not None
    assert isinstance(result, CategoriaModel)
    assert result.nombre == "Actualizado"
    mock_session.execute.assert_called_once() # get_by_id call
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(existing_categoria)

    # Arrange - Caso categoría no existe
    mock_session.reset_mock()
    mock_result.scalars.return_value.first.return_value = None

    # Act
    result = await repository.update(categoria_id, nombre="No existe")

    # Assert
    assert result is None

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.update(categoria_id, nombre="Error")

    # mock_session.rollback.assert_called_once() # get_by_id might not rollback on select error depending on impl, but BaseRepository.update catches and rolls back?
    # BaseRepository.update calls get_by_id. If get_by_id raises, update propagates it.
    # BaseRepository.get_by_id raises SQLAlchemyError directly.
    # So update catches it? No, update calls get_by_id inside try block.
    # If get_by_id raises, it goes to except block of update, which calls rollback.
    # Wait, get_by_id in BaseRepository:
    # try: execute... except: raise e
    # update in BaseRepository:
    # try: get_by_id... except: rollback; raise
    # So yes, rollback should be called.
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_all():
    """
    Verifica que el método get_all retorna correctamente una lista paginada de categorías.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar los mocks para simular la respuesta de la base de datos.
        - Llamar al método get_all con parámetros de paginación.
        - Verificar que se retorne la lista y el total correctos.

    POSTCONDICIONES:
        - El método debe retornar una tupla con lista y total.
        - La lista debe contener objetos CategoriaModel.
        - El total debe ser correcto.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_count_result = MagicMock()
    
    categorias = [
        CategoriaModel(id=str(ULID()), nombre="Categoria1"),
        CategoriaModel(id=str(ULID()), nombre="Categoria2")
    ]
    mock_result.scalars.return_value.all.return_value = categorias
    mock_count_result.scalar.return_value = 2
    
    # BaseRepository._fetch_paginated executes count query FIRST, then data query
    mock_session.execute.side_effect = [mock_count_result, mock_result]

    repository = CategoriaRepository(mock_session)

    # Act
    result, total = await repository.get_all(skip=0, limit=10)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(cat, CategoriaModel) for cat in result)
    assert total == 2
    assert mock_session.execute.call_count == 2

