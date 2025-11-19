"""
Pruebas unitarias para el repositorio de relaciones producto-alérgeno.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del repositorio encargado de las operaciones CRUD relacionadas con las asignaciones
de alérgenos a productos del menú. Se utilizan mocks para simular la capa de base de datos.

PRECONDICIONES:
    - Los módulos ProductoAlergenoRepository y ProductoAlergenoModel deben estar correctamente implementados.
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

from src.repositories.menu.producto_alergeno_repository import ProductoAlergenoRepository
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.core.enums.alergeno_enums import NivelPresencia

# Importar modelos relacionados para resolver dependencias de SQLAlchemy
from src.models.menu.producto_model import ProductoModel  # noqa: F401
from src.models.menu.alergeno_model import AlergenoModel  # noqa: F401


@pytest.mark.asyncio
async def test_get_by_id():
    """
    Verifica que el método get_by_id recupera correctamente una relación por su ID único.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para el ID de la relación.

    PROCESO:
        - Configurar el mock para simular la respuesta de la base de datos.
        - Llamar al método get_by_id con el ID específico.
        - Verificar que se ejecute la consulta correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar un objeto ProductoAlergenoModel cuando existe la relación.
        - El método debe retornar None cuando no existe la relación.
        - La consulta SQL debe formarse correctamente con el ID único.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()

    id_producto = str(ULID())
    id_alergeno = str(ULID())
    id_relacion = str(ULID())  # ID único de la relación

    producto_alergeno = ProductoAlergenoModel(
        id_producto=id_producto,
        id_alergeno=id_alergeno,
        nivel_presencia=NivelPresencia.CONTIENE,
        notas="Test allergen"
    )
    # El ID ya se autogenera en __init__, pero lo sobreescribimos para el test
    producto_alergeno.id = id_relacion

    mock_result.scalars.return_value.first.return_value = producto_alergeno
    mock_session.execute.return_value = mock_result

    repository = ProductoAlergenoRepository(mock_session)

    # Act
    result = await repository.get_by_id(id_relacion)

    # Assert
    assert result is not None
    assert isinstance(result, ProductoAlergenoModel)
    assert result.id == id_relacion
    assert result.id_producto == id_producto
    assert result.id_alergeno == id_alergeno
    mock_session.execute.assert_called_once()

    # Prueba de caso negativo
    mock_result.scalars.return_value.first.return_value = None
    result = await repository.get_by_id(str(ULID()))
    assert result is None


@pytest.mark.asyncio
async def test_create_producto_alergeno():
    """
    Verifica que el método create persiste correctamente una relación en la base de datos.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un objeto ProductoAlergenoModel válido para crear.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método create con una instancia de ProductoAlergenoModel.
        - Verificar que se realicen todas las operaciones necesarias para persistir el objeto.

    POSTCONDICIONES:
        - El método debe añadir la relación a la sesión.
        - El método debe hacer flush, commit y refresh.
        - El método debe retornar la relación creada.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    producto_alergeno = ProductoAlergenoModel(
        id_producto=str(ULID()),
        id_alergeno=str(ULID()),
        nivel_presencia=NivelPresencia.TRAZAS,
        notas="Contiene trazas por contaminación cruzada"
    )
    repository = ProductoAlergenoRepository(mock_session)

    # Act
    result = await repository.create(producto_alergeno)

    # Assert - Caso exitoso
    assert result is not None
    assert result == producto_alergeno
    mock_session.add.assert_called_once_with(producto_alergeno)
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(producto_alergeno)

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.flush.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.create(producto_alergeno)

    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_producto_alergeno():
    """
    Verifica que el método delete elimina correctamente una relación por su ID único.

    PRECONDICIONES:
        - Se debe tener una instancia mock de AsyncSession.
        - Se debe tener un ULID válido para el ID de la relación.

    PROCESO:
        - Configurar los mocks para simular el comportamiento de la base de datos.
        - Llamar al método delete con el ID específico.
        - Verificar que se ejecute la sentencia correcta y se retorne el resultado esperado.

    POSTCONDICIONES:
        - El método debe retornar True cuando se elimina una relación existente.
        - El método debe retornar False cuando no existe la relación a eliminar.
        - En caso de error, debe hacer rollback y propagar la excepción.
    """
    # Arrange - Caso exitoso (se elimina la relación)
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1  # Simula que se eliminó una fila
    mock_session.execute.return_value = mock_result

    id_relacion = str(ULID())
    repository = ProductoAlergenoRepository(mock_session)

    # Act
    result = await repository.delete(id_relacion)

    # Assert
    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso relación no existe
    mock_session.reset_mock()
    mock_result.rowcount = 0  # Simula que no se eliminó ninguna fila

    # Act
    result = await repository.delete(id_relacion)

    # Assert
    assert result is False
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()

    # Arrange - Caso de error
    mock_session.reset_mock()
    mock_session.execute.side_effect = SQLAlchemyError("Error de prueba")

    # Act & Assert - Caso de error
    with pytest.raises(SQLAlchemyError):
        await repository.delete(id_relacion)

    mock_session.rollback.assert_called_once()
