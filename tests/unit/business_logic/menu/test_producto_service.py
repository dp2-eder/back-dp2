"""
Pruebas unitarias para el servicio de productos.
"""
from ulid import ULID
import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from datetime import datetime


from src.business_logic.menu.producto_service import ProductoService
from src.models.menu.producto_model import ProductoModel
from src.api.schemas.producto_schema import ProductoCreate, ProductoUpdate
from src.business_logic.exceptions.producto_exceptions import (
    ProductoValidationError,
    ProductoNotFoundError,
    ProductoConflictError,
)
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repository():
    """
    Fixture que proporciona un mock del repositorio de productos.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def producto_service(mock_repository):
    """
    Fixture que proporciona una instancia del servicio de productos con un repositorio mockeado.
    """
    service = ProductoService(AsyncMock())
    service.repository = mock_repository
    return service


@pytest.fixture
def sample_producto_data():
    """
    Fixture que proporciona datos de muestra para un producto.
    """
    return {
        "id": str(ULID()),
        "id_categoria": str(ULID()),
        "nombre": "Test Producto",
        "descripcion": "Producto para pruebas",
        "precio_base": Decimal("15.99"),
        "imagen_path": "/images/test.jpg",
        "imagen_alt_text": "Test image",
        "disponible": True,
        "destacado": False,
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.mark.asyncio
async def test_create_producto_success(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la creación exitosa de un producto.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Llama al método create_producto con datos válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe crear el producto correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    producto_create = ProductoCreate(
        id_categoria=sample_producto_data["id_categoria"],
        nombre=sample_producto_data["nombre"],
        descripcion=sample_producto_data["descripcion"],
        precio_base=sample_producto_data["precio_base"],
        imagen_path=sample_producto_data["imagen_path"],
        imagen_alt_text=sample_producto_data["imagen_alt_text"],
    )
    mock_repository.create.return_value = ProductoModel(**sample_producto_data)

    # Act
    result = await producto_service.create_producto(producto_create)

    # Assert
    assert result.id == sample_producto_data["id"]
    assert result.nombre == sample_producto_data["nombre"]
    assert result.descripcion == sample_producto_data["descripcion"]
    assert result.precio_base == sample_producto_data["precio_base"]
    mock_repository.create.assert_called_once()

    # Verificar que se pasó un objeto ProductoModel al repositorio
    args, _ = mock_repository.create.call_args
    assert isinstance(args[0], ProductoModel)
    assert args[0].nombre == sample_producto_data["nombre"]
    assert args[0].descripcion == sample_producto_data["descripcion"]
    assert args[0].precio_base == sample_producto_data["precio_base"]


@pytest.mark.asyncio
async def test_create_producto_duplicate_name(producto_service, mock_repository, sample_producto_data):
    """
    Prueba el manejo de errores al intentar crear un producto con nombre duplicado.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular un error de integridad.
        - Llama al método create_producto con un nombre duplicado.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoConflictError.
    """
    # Arrange
    producto_create = ProductoCreate(
        id_categoria=sample_producto_data["id_categoria"],
        nombre=sample_producto_data["nombre"],
        descripcion=sample_producto_data["descripcion"],
        precio_base=sample_producto_data["precio_base"],
    )
    mock_repository.create.side_effect = IntegrityError(
        statement="Duplicate entry", params={}, orig=Exception("Duplicate entry")
    )

    # Act & Assert
    with pytest.raises(ProductoConflictError) as excinfo:
        await producto_service.create_producto(producto_create)

    assert "Ya existe un producto con el nombre" in str(excinfo.value)
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_producto_by_id_success(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la obtención exitosa de un producto por su ID.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia del producto.
        - Llama al método get_producto_by_id con un ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar el producto correctamente.
        - El repositorio debe ser llamado con el ID correcto.
    """
    # Arrange
    producto_id = sample_producto_data["id"]
    mock_repository.get_by_id.return_value = ProductoModel(**sample_producto_data)

    # Act
    result = await producto_service.get_producto_by_id(producto_id)

    # Assert
    assert result.id == producto_id
    assert result.nombre == sample_producto_data["nombre"]
    assert result.descripcion == sample_producto_data["descripcion"]
    assert result.precio_base == sample_producto_data["precio_base"]
    mock_repository.get_by_id.assert_called_once_with(producto_id)


@pytest.mark.asyncio
async def test_get_producto_by_id_not_found(producto_service, mock_repository):
    """
    Prueba el manejo de errores al intentar obtener un producto que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el producto no existe.
        - Llama al método get_producto_by_id con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoNotFoundError.
    """
    # Arrange
    producto_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ProductoNotFoundError) as excinfo:
        await producto_service.get_producto_by_id(producto_id)

    assert f"No se encontró el producto con ID {producto_id}" in str(excinfo.value)
    mock_repository.get_by_id.assert_called_once_with(producto_id)


@pytest.mark.asyncio
async def test_delete_producto_success(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la eliminación exitosa de un producto.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia y eliminación exitosa del producto.
        - Llama al método delete_producto con un ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe eliminar el producto correctamente.
        - El repositorio debe ser llamado con el ID correcto.
    """
    # Arrange
    producto_id = sample_producto_data["id"]
    mock_repository.get_by_id.return_value = ProductoModel(**sample_producto_data)
    mock_repository.delete.return_value = True

    # Act
    result = await producto_service.delete_producto(producto_id)

    # Assert
    assert result is True
    mock_repository.get_by_id.assert_called_once_with(producto_id)
    mock_repository.delete.assert_called_once_with(producto_id)


@pytest.mark.asyncio
async def test_delete_producto_not_found(producto_service, mock_repository):
    """
    Prueba el manejo de errores al intentar eliminar un producto que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el producto no existe.
        - Llama al método delete_producto con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoNotFoundError.
    """
    # Arrange
    producto_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ProductoNotFoundError) as excinfo:
        await producto_service.delete_producto(producto_id)

    assert f"No se encontró el producto con ID {producto_id}" in str(excinfo.value)
    mock_repository.get_by_id.assert_called_once_with(producto_id)
    mock_repository.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_productos_success(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la obtención exitosa de una lista paginada de productos.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una lista de productos.
        - Llama al método get_productos con parámetros válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de productos correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    productos = [
        ProductoModel(**sample_producto_data),
        ProductoModel(
            id=str(ULID()),
            id_categoria=str(ULID()),
            nombre="Otro Producto",
            descripcion="Otro producto para pruebas",
            precio_base=Decimal("20.00"),
            disponible=True,
            destacado=False,
        ),
    ]
    mock_repository.get_all.return_value = (productos, len(productos))

    # Act
    result = await producto_service.get_productos(skip=0, limit=10)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].nombre == sample_producto_data["nombre"]
    assert result.items[1].nombre == "Otro Producto"
    mock_repository.get_all.assert_called_once_with(0, 10, None)


@pytest.mark.asyncio
async def test_get_productos_validation_error(producto_service):
    """
    Prueba el manejo de errores al proporcionar parámetros inválidos para obtener productos.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Llama al método get_productos con parámetros inválidos.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoValidationError.
    """
    # Act & Assert - Parámetro skip negativo
    with pytest.raises(ProductoValidationError) as excinfo:
        await producto_service.get_productos(skip=-1, limit=10)
    assert "El parámetro 'skip' debe ser mayor o igual a cero" in str(excinfo.value)

    # Act & Assert - Parámetro limit no positivo
    with pytest.raises(ProductoValidationError) as excinfo:
        await producto_service.get_productos(skip=0, limit=0)
    assert "El parámetro 'limit' debe ser mayor a cero" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_productos_with_categoria_filter(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la obtención exitosa de una lista paginada de productos filtrados por categoría.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una lista de productos de una categoría específica.
        - Llama al método get_productos con un filtro de categoría.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de productos filtrados correctamente.
        - El repositorio debe ser llamado con el id_categoria correcto.
    """
    # Arrange
    id_categoria = str(ULID())
    productos = [
        ProductoModel(**sample_producto_data),
    ]
    mock_repository.get_all.return_value = (productos, len(productos))

    # Act
    result = await producto_service.get_productos(skip=0, limit=10, id_categoria=id_categoria)

    # Assert
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].nombre == sample_producto_data["nombre"]
    mock_repository.get_all.assert_called_once_with(0, 10, id_categoria)


@pytest.mark.asyncio
async def test_update_producto_success(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la actualización exitosa de un producto.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la actualización exitosa de un producto.
        - Llama al método update_producto con datos válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe actualizar el producto correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    producto_id = sample_producto_data["id"]
    update_data = ProductoUpdate(
        nombre="Producto Actualizado", descripcion="Descripción actualizada"
    )

    updated_producto = ProductoModel(
        **{
            **sample_producto_data,
            "nombre": "Producto Actualizado",
            "descripcion": "Descripción actualizada",
        }
    )
    mock_repository.update.return_value = updated_producto
    mock_repository.get_by_id.return_value = updated_producto

    # Act
    result = await producto_service.update_producto(producto_id, update_data)

    # Assert
    assert result.id == producto_id
    assert result.nombre == "Producto Actualizado"
    assert result.descripcion == "Descripción actualizada"
    mock_repository.update.assert_called_once_with(
        producto_id, nombre="Producto Actualizado", descripcion="Descripción actualizada"
    )


@pytest.mark.asyncio
async def test_update_producto_not_found(producto_service, mock_repository):
    """
    Prueba el manejo de errores al intentar actualizar un producto que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el producto no existe.
        - Llama al método update_producto con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoNotFoundError.
    """
    # Arrange
    producto_id = str(ULID())
    update_data = ProductoUpdate(nombre="Producto Actualizado")
    mock_repository.update.return_value = None

    # Act & Assert
    with pytest.raises(ProductoNotFoundError) as excinfo:
        await producto_service.update_producto(producto_id, update_data)

    assert f"No se encontró el producto con ID {producto_id}" in str(excinfo.value)
    mock_repository.update.assert_called_once_with(producto_id, nombre="Producto Actualizado")


@pytest.mark.asyncio
async def test_update_producto_duplicate_name(producto_service, mock_repository, sample_producto_data):
    """
    Prueba el manejo de errores al intentar actualizar un producto con un nombre duplicado.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular un error de integridad.
        - Llama al método update_producto con un nombre duplicado.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoConflictError.
    """
    # Arrange
    producto_id = sample_producto_data["id"]
    update_data = ProductoUpdate(nombre="Producto Duplicado")
    mock_repository.update.side_effect = IntegrityError(
        statement="Duplicate entry", params={}, orig=Exception("Duplicate entry")
    )

    # Act & Assert
    with pytest.raises(ProductoConflictError) as excinfo:
        await producto_service.update_producto(producto_id, update_data)

    assert "Ya existe un producto con el nombre" in str(excinfo.value)
    mock_repository.update.assert_called_once_with(producto_id, nombre="Producto Duplicado")


@pytest.mark.asyncio
async def test_update_producto_no_changes(producto_service, mock_repository, sample_producto_data):
    """
    Prueba la actualización de un producto cuando no se proporcionan cambios.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia del producto.
        - Llama al método update_producto sin proporcionar campos para actualizar.
        - Verifica que se recupere el producto existente sin cambios.

    POSTCONDICIONES:
        - El servicio debe retornar el producto existente sin modificaciones.
        - El método update del repositorio no debe ser llamado.
    """
    # Arrange
    producto_id = sample_producto_data["id"]
    update_data = ProductoUpdate()  # Sin datos para actualizar
    mock_repository.get_by_id.return_value = ProductoModel(**sample_producto_data)

    # Act
    result = await producto_service.update_producto(producto_id, update_data)

    # Assert
    assert result.id == producto_id
    assert result.nombre == sample_producto_data["nombre"]
    mock_repository.get_by_id.assert_called_once_with(producto_id)
    mock_repository.update.assert_not_called()
