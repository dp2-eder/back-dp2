"""
Pruebas unitarias para el servicio de locales.
"""

import pytest
from unittest.mock import AsyncMock
from ulid import ULID
from datetime import datetime, date

from src.business_logic.mesas.local_service import LocalService
from src.models.mesas.local_model import LocalModel
from src.core.enums.local_enums import TipoLocal
from src.api.schemas.local_schema import LocalCreate, LocalUpdate
from src.business_logic.exceptions.local_exceptions import (
    LocalValidationError,
    LocalNotFoundError,
    LocalConflictError,
)
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repository():
    """
    Fixture que proporciona un mock del repositorio de locales.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def local_service(mock_repository):
    """
    Fixture que proporciona una instancia del servicio de locales con un repositorio mockeado.
    """
    service = LocalService(AsyncMock())
    service.repository = mock_repository
    return service


@pytest.fixture
def sample_local_data():
    """
    Fixture que proporciona datos de muestra para un local.
    """
    return {
        "id": str(ULID()),
        "codigo": "CEV-001",
        "nombre": "La Cevichería del Centro",
        "direccion": "Av. Principal 123",
        "distrito": "Miraflores",
        "ciudad": "Lima",
        "telefono": "01-2345678",
        "email": "contacto@cevicheria.com",
        "tipo_local": TipoLocal.CENTRAL,
        "capacidad_total": 100,
        "activo": True,
        "fecha_apertura": date(2024, 1, 15),
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.mark.asyncio
async def test_create_local_success(local_service, mock_repository, sample_local_data):
    """
    Prueba la creación exitosa de un local.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Llama al método create_local con datos válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe crear el local correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    local_create = LocalCreate(
        codigo=sample_local_data["codigo"],
        nombre=sample_local_data["nombre"],
        direccion=sample_local_data["direccion"],
        distrito=sample_local_data["distrito"],
        ciudad=sample_local_data["ciudad"],
        telefono=sample_local_data["telefono"],
        email=sample_local_data["email"],
        tipo_local=sample_local_data["tipo_local"],
        capacidad_total=sample_local_data["capacidad_total"],
        fecha_apertura=sample_local_data["fecha_apertura"],
    )
    mock_repository.create.return_value = LocalModel(**sample_local_data)

    # Act
    result = await local_service.create_local(local_create)

    # Assert
    assert result.id == sample_local_data["id"]
    assert result.codigo == sample_local_data["codigo"]
    assert result.nombre == sample_local_data["nombre"]
    assert result.tipo_local == sample_local_data["tipo_local"]
    mock_repository.create.assert_called_once()

    # Verificar que se pasó un objeto LocalModel al repositorio
    args, _ = mock_repository.create.call_args
    assert isinstance(args[0], LocalModel)
    assert args[0].codigo == sample_local_data["codigo"]
    assert args[0].nombre == sample_local_data["nombre"]


@pytest.mark.asyncio
async def test_create_local_duplicate_codigo(
    local_service, mock_repository, sample_local_data
):
    """
    Prueba el manejo de errores al intentar crear un local con código duplicado.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular un error de integridad.
        - Llama al método create_local con un código duplicado.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalConflictError.
    """
    # Arrange
    local_create = LocalCreate(
        codigo=sample_local_data["codigo"],
        nombre=sample_local_data["nombre"],
        direccion=sample_local_data["direccion"],
        tipo_local=sample_local_data["tipo_local"],
    )
    mock_repository.create.side_effect = IntegrityError(
        statement="Duplicate entry", params={}, orig=Exception("Duplicate entry")
    )

    # Act & Assert
    with pytest.raises(LocalConflictError) as excinfo:
        await local_service.create_local(local_create)

    assert "Ya existe un local con el código" in str(excinfo.value)
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_local_by_id_success(local_service, mock_repository, sample_local_data):
    """
    Prueba la obtención exitosa de un local por su ID.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia del local.
        - Llama al método get_local_by_id con un ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar el local correctamente.
        - El repositorio debe ser llamado con el ID correcto.
    """
    # Arrange
    local_id = sample_local_data["id"]
    mock_repository.get_by_id.return_value = LocalModel(**sample_local_data)

    # Act
    result = await local_service.get_local_by_id(local_id)

    # Assert
    assert result.id == local_id
    assert result.codigo == sample_local_data["codigo"]
    assert result.nombre == sample_local_data["nombre"]
    mock_repository.get_by_id.assert_called_once_with(local_id)


@pytest.mark.asyncio
async def test_get_local_by_id_not_found(local_service, mock_repository):
    """
    Prueba el manejo de errores al intentar obtener un local que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Llama al método get_local_by_id con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalNotFoundError.
    """
    # Arrange
    local_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(LocalNotFoundError) as excinfo:
        await local_service.get_local_by_id(local_id)

    assert f"No se encontró el local con ID {local_id}" in str(excinfo.value)
    mock_repository.get_by_id.assert_called_once_with(local_id)


@pytest.mark.asyncio
async def test_get_local_by_codigo_success(
    local_service, mock_repository, sample_local_data
):
    """
    Prueba la obtención exitosa de un local por su código.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia del local.
        - Llama al método get_local_by_codigo con un código válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar el local correctamente.
        - El repositorio debe ser llamado con el código correcto.
    """
    # Arrange
    codigo = sample_local_data["codigo"]
    mock_repository.get_by_codigo.return_value = LocalModel(**sample_local_data)

    # Act
    result = await local_service.get_local_by_codigo(codigo)

    # Assert
    assert result.codigo == codigo
    assert result.nombre == sample_local_data["nombre"]
    mock_repository.get_by_codigo.assert_called_once_with(codigo)


@pytest.mark.asyncio
async def test_get_local_by_codigo_not_found(local_service, mock_repository):
    """
    Prueba el manejo de errores al intentar obtener un local por código inexistente.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Llama al método get_local_by_codigo con un código inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalNotFoundError.
    """
    # Arrange
    codigo = "CEV-999"
    mock_repository.get_by_codigo.return_value = None

    # Act & Assert
    with pytest.raises(LocalNotFoundError) as excinfo:
        await local_service.get_local_by_codigo(codigo)

    assert f"No se encontró el local con código '{codigo}'" in str(excinfo.value)
    mock_repository.get_by_codigo.assert_called_once_with(codigo)


@pytest.mark.asyncio
async def test_delete_local_success(local_service, mock_repository, sample_local_data):
    """
    Prueba la eliminación exitosa de un local.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia y eliminación exitosa del local.
        - Llama al método delete_local con un ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe eliminar el local correctamente.
        - El repositorio debe ser llamado con el ID correcto.
    """
    # Arrange
    local_id = sample_local_data["id"]
    mock_repository.get_by_id.return_value = LocalModel(**sample_local_data)
    mock_repository.delete.return_value = True

    # Act
    result = await local_service.delete_local(local_id)

    # Assert
    assert result is True
    mock_repository.get_by_id.assert_called_once_with(local_id)
    mock_repository.delete.assert_called_once_with(local_id)


@pytest.mark.asyncio
async def test_delete_local_not_found(local_service, mock_repository):
    """
    Prueba el manejo de errores al intentar eliminar un local que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Llama al método delete_local con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalNotFoundError.
    """
    # Arrange
    local_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(LocalNotFoundError) as excinfo:
        await local_service.delete_local(local_id)

    assert f"No se encontró el local con ID {local_id}" in str(excinfo.value)
    mock_repository.get_by_id.assert_called_once_with(local_id)
    mock_repository.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_locales_success(local_service, mock_repository, sample_local_data):
    """
    Prueba la obtención exitosa de una lista paginada de locales.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una lista de locales.
        - Llama al método get_locales con parámetros válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de locales correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    locales = [
        LocalModel(**sample_local_data),
        LocalModel(
            id=str(ULID()),
            codigo="CEV-002",
            nombre="Otro Local",
            direccion="Otra Dirección",
            tipo_local=TipoLocal.SUCURSAL,
            activo=True,
        ),
    ]
    mock_repository.get_all.return_value = (locales, len(locales))

    # Act
    result = await local_service.get_locales(skip=0, limit=10)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].codigo == sample_local_data["codigo"]
    assert result.items[1].codigo == "CEV-002"
    mock_repository.get_all.assert_called_once_with(0, 10)


@pytest.mark.asyncio
async def test_get_locales_validation_error(local_service):
    """
    Prueba el manejo de errores al proporcionar parámetros inválidos para obtener locales.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Llama al método get_locales con parámetros inválidos.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalValidationError.
    """
    # Act & Assert - Parámetro skip negativo
    with pytest.raises(LocalValidationError) as excinfo:
        await local_service.get_locales(skip=-1, limit=10)
    assert "El parámetro 'skip' debe ser mayor o igual a cero" in str(excinfo.value)

    # Act & Assert - Parámetro limit no positivo
    with pytest.raises(LocalValidationError) as excinfo:
        await local_service.get_locales(skip=0, limit=0)
    assert "El parámetro 'limit' debe ser mayor a cero" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_local_success(local_service, mock_repository, sample_local_data):
    """
    Prueba la actualización exitosa de un local.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la actualización exitosa de un local.
        - Llama al método update_local con datos válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe actualizar el local correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    local_id = sample_local_data["id"]
    update_data = LocalUpdate(
        nombre="Local Actualizado", direccion="Dirección Actualizada"
    )

    updated_local = LocalModel(
        **{
            **sample_local_data,
            "nombre": "Local Actualizado",
            "direccion": "Dirección Actualizada",
        }
    )
    mock_repository.update.return_value = updated_local

    # Act
    result = await local_service.update_local(local_id, update_data)

    # Assert
    assert result.id == local_id
    assert result.nombre == "Local Actualizado"
    assert result.direccion == "Dirección Actualizada"
    mock_repository.update.assert_called_once_with(
        local_id, nombre="Local Actualizado", direccion="Dirección Actualizada"
    )


@pytest.mark.asyncio
async def test_update_local_not_found(local_service, mock_repository):
    """
    Prueba el manejo de errores al intentar actualizar un local que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Llama al método update_local con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalNotFoundError.
    """
    # Arrange
    local_id = str(ULID())
    update_data = LocalUpdate(nombre="Local Actualizado")
    mock_repository.update.return_value = None

    # Act & Assert
    with pytest.raises(LocalNotFoundError) as excinfo:
        await local_service.update_local(local_id, update_data)

    assert f"No se encontró el local con ID {local_id}" in str(excinfo.value)
    mock_repository.update.assert_called_once_with(local_id, nombre="Local Actualizado")


@pytest.mark.asyncio
async def test_update_local_duplicate_codigo(
    local_service, mock_repository, sample_local_data
):
    """
    Prueba el manejo de errores al intentar actualizar un local con un código duplicado.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular un error de integridad.
        - Llama al método update_local con un código duplicado.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar LocalConflictError.
    """
    # Arrange
    local_id = sample_local_data["id"]
    update_data = LocalUpdate(codigo="CEV-999")
    mock_repository.update.side_effect = IntegrityError(
        statement="Duplicate entry", params={}, orig=Exception("Duplicate entry")
    )

    # Act & Assert
    with pytest.raises(LocalConflictError) as excinfo:
        await local_service.update_local(local_id, update_data)

    assert "Ya existe un local con el código" in str(excinfo.value)
    mock_repository.update.assert_called_once_with(local_id, codigo="CEV-999")


@pytest.mark.asyncio
async def test_update_local_no_changes(local_service, mock_repository, sample_local_data):
    """
    Prueba la actualización de un local cuando no se proporcionan cambios.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia del local.
        - Llama al método update_local sin proporcionar campos para actualizar.
        - Verifica que se recupere el local existente sin cambios.

    POSTCONDICIONES:
        - El servicio debe retornar el local existente sin modificaciones.
        - El método update del repositorio no debe ser llamado.
    """
    # Arrange
    local_id = sample_local_data["id"]
    update_data = LocalUpdate()  # Sin datos para actualizar
    mock_repository.get_by_id.return_value = LocalModel(**sample_local_data)

    # Act
    result = await local_service.update_local(local_id, update_data)

    # Assert
    assert result.id == local_id
    assert result.codigo == sample_local_data["codigo"]
    mock_repository.get_by_id.assert_called_once_with(local_id)
    mock_repository.update.assert_not_called()
