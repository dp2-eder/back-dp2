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
        CategoriaModel(id=str(ULID()), nombre="Categoria2"),
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
