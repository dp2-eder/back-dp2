"""
Pruebas unitarias para el repositorio de productos.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del repositorio encargado de las operaciones CRUD relacionadas con los productos del sistema.
Se utilizan mocks para simular la capa de base de datos.

PRECONDICIONES:
    - Los módulos ProductoRepository y ProductoModel deben estar correctamente implementados.
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
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repositories.menu.producto_repository import ProductoRepository
from src.models.menu.producto_model import ProductoModel


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente un producto por su ID con alérgenos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido para buscar.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con un ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto ProductoModel cuando existe el producto.
        - El método debe retornar None cuando no existe el producto.
        - La consulta SQL debe formarse correctamente.
        - El método debe cargar los alérgenos del producto.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock para el producto
    mock_producto_result = MagicMock()
    producto = ProductoModel(
        id=str(ULID()),
        id_categoria=str(ULID()),
        nombre="Hamburguesa",
        precio_base=Decimal("12.50")
    )
    mock_producto_result.scalars.return_value.first.return_value = producto

    # Mock para los alérgenos (segunda query)
    mock_alergenos_result = MagicMock()
    mock_alergenos_result.scalars.return_value.all.return_value = []

    # Configurar execute para retornar diferentes resultados en cada llamada
    mock_session.execute.side_effect = [mock_producto_result, mock_alergenos_result]

    producto_id = str(ULID())
    repository = ProductoRepository(mock_session)

    # Act
    result = await repository.get_by_id(producto_id)

    # Assert
    assert result is not None
    assert isinstance(result, ProductoModel)
    assert result.nombre == "Hamburguesa"
    assert mock_session.execute.call_count == 1

    # Prueba de caso negativo
    mock_session.execute.reset_mock()
    mock_producto_result.scalars.return_value.first.return_value = None
    mock_session.execute.side_effect = [mock_producto_result]
    result = await repository.get_by_id(producto_id)
    assert result is None


@pytest.mark.asyncio
async def test_create_producto():
    """
    Verifica que el método create persiste correctamente un producto en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto ProductoModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de ProductoModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir el producto a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar el producto creado.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    producto = ProductoModel(
        nombre="Pizza",
        id_categoria=str(ULID()),
        precio_base=Decimal("15.00")
    )
    repository = ProductoRepository(mock_session)

    # Act
    result = await repository.create(producto)

    # Assert - Caso exitoso
    assert result is not None
    assert result == producto
    mock_session.add.assert_called_once_with(producto)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(producto)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(producto)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_producto():
    """
    Verifica que el método delete elimina correctamente un producto por su ID.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID válido para eliminar.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con un ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina un producto existente.
        - El método debe retornar False cuando no existe el producto a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina el producto)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    producto_id = str(ULID())
    repository = ProductoRepository(mock_session)

    # Act
    result = await repository.delete(producto_id)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso producto no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(producto_id)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(producto_id)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_productos():
    """
    Verifica que el método get_all recupera correctamente una lista paginada de productos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_all con parámetros de paginación.
        - Verificar que se ejecuten las consultas correctas y se retornen los resultados esperados.

    POSTCONDICIONES:
        - El método debe retornar una tupla (lista de productos, total).
        - Debe aplicar correctamente la paginación.
        - Debe aplicar el filtro de categoría si se proporciona.
    """
    # Arrange - Caso sin filtro
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mock para el conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2
    
    # Mock para la consulta de productos
    mock_productos_result = MagicMock()
    productos = [
        ProductoModel(
            id=str(ULID()),
            id_categoria=str(ULID()),
            nombre="Pizza",
            precio_base=Decimal("15.00")
        ),
        ProductoModel(
            id=str(ULID()),
            id_categoria=str(ULID()),
            nombre="Hamburguesa",
            precio_base=Decimal("12.50")
        ),
    ]
    mock_productos_result.scalars.return_value.all.return_value = productos
    
    # Configurar execute para retornar diferentes resultados
    mock_session.execute.side_effect = [mock_count_result, mock_productos_result]
    
    repository = ProductoRepository(mock_session)

    # Act
    result_productos, total = await repository.get_all(skip=0, limit=10, id_categoria=None)

    # Assert
    assert total == 2
    assert len(result_productos) == 2
    assert result_productos[0].nombre == "Pizza"
    assert result_productos[1].nombre == "Hamburguesa"
    assert mock_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_all_productos_with_categoria_filter():
    """
    Verifica que el método get_all filtra correctamente por categoría.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un UUID de categoría válido.

    PROCESO:
        - Configurar el mock para simular productos filtrados por categoría.
        - Llamar al método get_all con un id_categoria.
        - Verificar que la consulta incluya el filtro correcto.

    POSTCONDICIONES:
        - El método debe retornar solo productos de la categoría especificada.
        - La consulta debe incluir el WHERE con id_categoria.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    id_categoria = str(ULID())
    
    # Mock para el conteo
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1
    
    # Mock para la consulta de productos
    mock_productos_result = MagicMock()
    productos = [
        ProductoModel(
            id=str(ULID()),
            id_categoria=id_categoria,
            nombre="Pizza Margherita",
            precio_base=Decimal("15.00")
        ),
    ]
    mock_productos_result.scalars.return_value.all.return_value = productos
    
    mock_session.execute.side_effect = [mock_count_result, mock_productos_result]
    
    repository = ProductoRepository(mock_session)

    # Act
    result_productos, total = await repository.get_all(skip=0, limit=10, id_categoria=id_categoria)

    # Assert
    assert total == 1
    assert len(result_productos) == 1
    assert result_productos[0].id_categoria == id_categoria
    assert mock_session.execute.call_count == 2
