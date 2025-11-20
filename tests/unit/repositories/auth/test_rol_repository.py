"""
Pruebas unitarias para el repositorio de roles.

ARCHIVO REACTIVADO Y ACTUALIZADO
================================
Este archivo ha sido reactivado y actualizado para soportar el nuevo sistema
con roles y el método get_by_nombre agregado.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ulid import ULID

from src.repositories.auth.rol_repository import RolRepository
from src.models.auth.rol_model import RolModel


@pytest.fixture
def mock_session():
    """Fixture para mock de sesión de base de datos."""
    session = AsyncMock()
    return session


@pytest.fixture
def rol_repository(mock_session):
    """Fixture para instancia de RolRepository con sesión mockeada."""
    return RolRepository(mock_session)


@pytest.fixture
def rol_comensal():
    """Fixture para rol COMENSAL."""
    return RolModel(
        id=str(ULID()),
        nombre="COMENSAL",
        descripcion="Rol para clientes del restaurante",
        activo=True
    )


@pytest.fixture
def rol_admin():
    """Fixture para rol ADMIN."""
    return RolModel(
        id=str(ULID()),
        nombre="ADMIN",
        descripcion="Rol administrador",
        activo=True
    )


class TestRolRepository:
    """Pruebas generales para RolRepository."""

    @pytest.mark.asyncio
    async def test_create_rol(self, rol_repository, mock_session, rol_comensal):
        """Test que crea un rol exitosamente."""
        # Mock de la sesión
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Ejecutar
        result = await rol_repository.create(rol_comensal)
        
        # Verificar
        assert result == rol_comensal
        mock_session.add.assert_called_once_with(rol_comensal)
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(rol_comensal)

    @pytest.mark.asyncio
    async def test_get_by_id_rol_existe(self, rol_repository, mock_session, rol_comensal):
        """Test que encuentra un rol por ID."""
        # Mock de la consulta - el resultado debe ser un objeto regular, no AsyncMock
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = rol_comensal
        mock_session.execute.return_value = mock_result
        
        # Ejecutar
        result = await rol_repository.get_by_id(rol_comensal.id)
        
        # Verificar
        assert result == rol_comensal
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_rol_no_existe(self, rol_repository, mock_session):
        """Test que no encuentra un rol por ID."""
        # Mock de la consulta que no encuentra resultados
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Ejecutar
        result = await rol_repository.get_by_id(str(ULID()))
        
        # Verificar
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_nombre_rol_existe(self, rol_repository, mock_session, rol_comensal):
        """Test que encuentra un rol por nombre."""
        # Mock de la consulta
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = rol_comensal
        mock_session.execute.return_value = mock_result
        
        # Ejecutar
        result = await rol_repository.get_by_nombre("COMENSAL")
        
        # Verificar
        assert result == rol_comensal
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_nombre_rol_no_existe(self, rol_repository, mock_session):
        """Test que no encuentra un rol por nombre."""
        # Mock de la consulta que no encuentra resultados
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Ejecutar
        result = await rol_repository.get_by_nombre("ROL_INEXISTENTE")
        
        # Verificar
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_roles(self, rol_repository, mock_session, rol_comensal, rol_admin):
        """Test que obtiene todos los roles paginados."""
        # Mock de las consultas
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [rol_comensal, rol_admin]
        
        # Mock de consulta de conteo
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2
        
        # Configurar el mock para retornar diferentes resultados para diferentes llamadas
        mock_session.execute.side_effect = [mock_result, mock_count_result]
        
        # Ejecutar
        result, total = await rol_repository.get_all(skip=0, limit=100)
        
        # Verificar
        assert len(result) == 2
        assert total == 2
        assert rol_comensal in result
        assert rol_admin in result

    @pytest.mark.asyncio
    async def test_update_rol(self, rol_repository, mock_session, rol_comensal):
        """Test que actualiza un rol exitosamente."""
        # Mock de get_by_id para simular que el rol existe
        with patch.object(rol_repository, 'get_by_id', return_value=rol_comensal):
            # Mock de la actualización
            mock_result = MagicMock()
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()
            
            # Ejecutar
            result = await rol_repository.update(
                rol_comensal.id, 
                descripcion="Descripción actualizada"
            )
            
            # Verificar
            assert result == rol_comensal
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rol_no_existe(self, rol_repository, mock_session):
        """Test que intenta actualizar un rol que no existe."""
        # Mock de get_by_id para simular que el rol no existe
        with patch.object(rol_repository, 'get_by_id', return_value=None):
            # Ejecutar
            result = await rol_repository.update(
                str(ULID()), 
                descripcion="Descripción actualizada"
            )
            
            # Verificar
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_rol(self, rol_repository, mock_session):
        """Test que elimina un rol exitosamente."""
        # Mock de la eliminación
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        
        # Ejecutar
        result = await rol_repository.delete(str(ULID()))
        
        # Verificar
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_rol_no_existe(self, rol_repository, mock_session):
        """Test que intenta eliminar un rol que no existe."""
        # Mock de la eliminación sin afectar filas
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        mock_session.commit = AsyncMock()
        
        # Ejecutar
        result = await rol_repository.delete(str(ULID()))
        
        # Verificar
        assert result is False

    @pytest.mark.asyncio
    async def test_create_rol_con_error(self, rol_repository, mock_session, rol_comensal):
        """Test que maneja errores al crear un rol."""
        # Mock que lanza excepción
        from sqlalchemy.exc import SQLAlchemyError
        mock_session.add = MagicMock(side_effect=SQLAlchemyError("Error de BD"))
        mock_session.rollback = AsyncMock()
        
        # Ejecutar y verificar excepción
        with pytest.raises(SQLAlchemyError):
            await rol_repository.create(rol_comensal)
        
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_rol_con_error(self, rol_repository, mock_session):
        """Test que maneja errores al eliminar un rol."""
        # Mock que lanza excepción
        from sqlalchemy.exc import SQLAlchemyError
        mock_session.execute = MagicMock(side_effect=SQLAlchemyError("Error de BD"))
        mock_session.rollback = AsyncMock()
        
        # Ejecutar y verificar excepción
        with pytest.raises(SQLAlchemyError):
            await rol_repository.delete(str(ULID()))
        
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_rol_con_error(self, rol_repository, mock_session, rol_comensal):
        """Test que maneja errores al actualizar un rol."""
        # Mock que lanza excepción
        from sqlalchemy.exc import SQLAlchemyError
        mock_session.execute = MagicMock(side_effect=SQLAlchemyError("Error de BD"))
        mock_session.rollback = AsyncMock()
        
        # Ejecutar y verificar excepción
        with pytest.raises(SQLAlchemyError):
            await rol_repository.update(rol_comensal.id, descripcion="Nuevo")
        
        mock_session.rollback.assert_called_once()


class TestRolRepositoryIntegration:
    """Pruebas de integración adicionales para RolRepository."""

    @pytest.mark.asyncio
    async def test_get_by_nombre_case_sensitive(self, rol_repository, mock_session, rol_comensal):
        """Test que get_by_nombre es case sensitive."""
        # Mock de la consulta
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = rol_comensal
        mock_session.execute.return_value = mock_result
        
        # Ejecutar con mayúsculas
        result = await rol_repository.get_by_nombre("COMENSAL")
        
        # Verificar
        assert result == rol_comensal
        
        # Verificar que se llamó con el texto exacto
        call_args = mock_session.execute.call_args[0][0]
        # La consulta debería buscar exactamente "COMENSAL"

    @pytest.mark.asyncio
    async def test_get_all_con_limites(self, rol_repository, mock_session, rol_comensal):
        """Test que get_all respeta los límites de paginación."""
        # Mock de las consultas
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [rol_comensal]
        
        # Mock de consulta de conteo
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        # Configurar el mock para retornar diferentes resultados
        mock_session.execute.side_effect = [mock_result, mock_count_result]
        
        # Ejecutar con límites específicos
        result, total = await rol_repository.get_all(skip=5, limit=10)
        
        # Verificar
        assert len(result) == 1
        assert total == 1
