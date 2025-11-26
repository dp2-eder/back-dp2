"""
Tests de integración para sesiones compartidas en LoginService.
Verifica que múltiples usuarios puedan compartir la misma sesión de mesa.
También verifica validación de mesa y manejo de sesiones expiradas.
"""

import pytest
from datetime import datetime, timedelta

from src.business_logic.auth.login_service import LoginService
from src.api.schemas.login_schema import LoginRequest
from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.repositories.mesas.usuario_sesion_mesa_repository import UsuarioSesionMesaRepository
from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository
from src.business_logic.exceptions.mesa_exceptions import MesaNotFoundError


@pytest.mark.asyncio
class TestLoginServiceSesionesCompartidas:
    """Tests de integración para sesiones compartidas."""

    async def test_dos_usuarios_comparten_sesion_misma_mesa(self, db_session):
        """
        Test: Dos usuarios diferentes se loguean a la misma mesa
        y deben compartir el mismo token de sesión.
        """
        # Arrange
        # Crear mesa de prueba
        mesa = MesaModel(numero=10, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_service = LoginService(db_session)

        usuario1_data = LoginRequest(
            email="juan@correo.com",
            nombre="Juan Pérez"
        )
        usuario2_data = LoginRequest(
            email="maria@correo.com",
            nombre="María García"
        )

        # Act
        # Usuario 1 se loguea (crea la sesión)
        response1 = await login_service.login(usuario1_data, mesa.id)
        await db_session.commit()

        # Usuario 2 se loguea a la misma mesa
        response2 = await login_service.login(usuario2_data, mesa.id)
        await db_session.commit()

        # Assert
        # Ambos usuarios deben tener el MISMO token_sesion
        assert response1.token_sesion == response2.token_sesion
        # Ambos usuarios deben tener el MISMO id_sesion_mesa
        assert response1.id_sesion_mesa == response2.id_sesion_mesa
        # Pero diferentes id_usuario
        assert response1.id_usuario != response2.id_usuario
        # Ambos deben tener la misma fecha de expiración
        assert response1.fecha_expiracion == response2.fecha_expiracion

    async def test_tres_usuarios_comparten_sesion(self, db_session):
        """
        Test: Tres usuarios se loguean a la misma mesa
        y todos comparten el mismo token.
        """
        # Arrange
        mesa = MesaModel(numero=20, capacidad=6)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_service = LoginService(db_session)
        usuario_sesion_repo = UsuarioSesionMesaRepository(db_session)

        usuarios_data = [
            LoginRequest(email="user1@correo.com", nombre="Usuario 1"),
            LoginRequest(email="user2@correo.com", nombre="Usuario 2"),
            LoginRequest(email="user3@correo.com", nombre="Usuario 3"),
        ]

        # Act
        responses = []
        for usuario_data in usuarios_data:
            response = await login_service.login(usuario_data, mesa.id)
            await db_session.commit()
            responses.append(response)

        # Assert
        # Todos deben tener el mismo token
        assert responses[0].token_sesion == responses[1].token_sesion
        assert responses[1].token_sesion == responses[2].token_sesion

        # Todos deben tener el mismo id_sesion_mesa
        assert responses[0].id_sesion_mesa == responses[1].id_sesion_mesa
        assert responses[1].id_sesion_mesa == responses[2].id_sesion_mesa

        # Verificar que hay 3 usuarios en la sesión
        usuarios_en_sesion = await usuario_sesion_repo.get_usuarios_by_sesion(
            responses[0].id_sesion_mesa
        )
        assert len(usuarios_en_sesion) == 3

    async def test_mismo_usuario_login_multiple_veces_misma_mesa(self, db_session):
        """
        Test: El mismo usuario hace login varias veces a la misma mesa.
        Debe reutilizar la sesión existente sin crear duplicados.
        """
        # Arrange
        mesa = MesaModel(numero=30, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_service = LoginService(db_session)
        usuario_sesion_repo = UsuarioSesionMesaRepository(db_session)

        usuario_data = LoginRequest(
            email="repetido@correo.com",
            nombre="Usuario Repetido"
        )

        # Act
        # Login 1
        response1 = await login_service.login(usuario_data, mesa.id)
        await db_session.commit()

        # Login 2 (mismo usuario, misma mesa)
        response2 = await login_service.login(usuario_data, mesa.id)
        await db_session.commit()

        # Login 3 (mismo usuario, misma mesa)
        response3 = await login_service.login(usuario_data, mesa.id)
        await db_session.commit()

        # Assert
        # Todos deben tener el mismo token y sesión
        assert response1.token_sesion == response2.token_sesion == response3.token_sesion
        assert response1.id_sesion_mesa == response2.id_sesion_mesa == response3.id_sesion_mesa
        assert response1.id_usuario == response2.id_usuario == response3.id_usuario

        # Debe haber solo 1 asociación usuario-sesión (no duplicados)
        asociaciones = await usuario_sesion_repo.get_all_by_sesion(
            response1.id_sesion_mesa
        )
        assert len(asociaciones) == 1

    async def test_usuarios_diferentes_mesas_diferentes_sesiones(self, db_session):
        """
        Test: Usuarios en diferentes mesas tienen sesiones diferentes.
        """
        # Arrange
        mesa1 = MesaModel(numero=40, capacidad=4)
        mesa2 = MesaModel(numero=41, capacidad=4)
        db_session.add(mesa1)
        db_session.add(mesa2)
        await db_session.commit()
        await db_session.refresh(mesa1)
        await db_session.refresh(mesa2)

        login_service = LoginService(db_session)

        usuario1_data = LoginRequest(email="user_mesa1@correo.com", nombre="Usuario Mesa 1")
        usuario2_data = LoginRequest(email="user_mesa2@correo.com", nombre="Usuario Mesa 2")

        # Act
        response_mesa1 = await login_service.login(usuario1_data, mesa1.id)
        await db_session.commit()

        response_mesa2 = await login_service.login(usuario2_data, mesa2.id)
        await db_session.commit()

        # Assert
        # Tokens diferentes
        assert response_mesa1.token_sesion != response_mesa2.token_sesion
        # Sesiones diferentes
        assert response_mesa1.id_sesion_mesa != response_mesa2.id_sesion_mesa


@pytest.mark.asyncio
class TestLoginServiceValidacionMesa:
    """Tests de integración para validación de mesa."""

    async def test_login_mesa_no_existe_lanza_error(self, db_session):
        """
        Test: Login con ID de mesa que no existe debe lanzar MesaNotFoundError.
        """
        # Arrange
        login_service = LoginService(db_session)
        usuario_data = LoginRequest(
            email="test@correo.com",
            nombre="Test Usuario"
        )

        # Act & Assert
        with pytest.raises(MesaNotFoundError) as exc_info:
            await login_service.login(usuario_data, "ID_QUE_NO_EXISTE")

        assert exc_info.value.error_code == "MESA_NOT_FOUND"

    async def test_login_mesa_inactiva_lanza_error(self, db_session):
        """
        Test: Login con mesa inactiva debe lanzar MesaNotFoundError.
        """
        # Arrange
        mesa_inactiva = MesaModel(numero=99, capacidad=4, activo=False)
        db_session.add(mesa_inactiva)
        await db_session.commit()
        await db_session.refresh(mesa_inactiva)

        login_service = LoginService(db_session)
        usuario_data = LoginRequest(
            email="test@correo.com",
            nombre="Test Usuario"
        )

        # Act & Assert
        with pytest.raises(MesaNotFoundError) as exc_info:
            await login_service.login(usuario_data, mesa_inactiva.id)

        assert exc_info.value.error_code == "MESA_INACTIVE"


@pytest.mark.asyncio
class TestLoginServiceSesionExpirada:
    """Tests de integración para manejo de sesiones expiradas."""

    async def test_login_sesion_expirada_crea_nueva_y_finaliza_anterior(self, db_session):
        """
        Test: Cuando hay una sesión expirada, debe:
        1. Marcar la sesión expirada como FINALIZADA
        2. Crear una nueva sesión ACTIVA
        3. Retornar la nueva sesión
        """
        # Arrange
        mesa = MesaModel(numero=50, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_service = LoginService(db_session)
        sesion_repo = SesionMesaRepository(db_session)

        # Primer login - crea sesión
        usuario1_data = LoginRequest(
            email="user1@correo.com",
            nombre="Usuario 1"
        )
        response1 = await login_service.login(usuario1_data, mesa.id)
        await db_session.commit()

        # Simular que la sesión expiró: modificar fecha_inicio a 3 horas atrás
        sesion_original = await sesion_repo.get_by_id(response1.id_sesion_mesa)
        sesion_original.fecha_inicio = datetime.now() - timedelta(hours=3)
        await db_session.commit()
        await db_session.refresh(sesion_original)

        # Verificar que la sesión está expirada
        assert sesion_original.esta_expirada() is True

        # Act - Segundo login con sesión expirada
        usuario2_data = LoginRequest(
            email="user2@correo.com",
            nombre="Usuario 2"
        )
        response2 = await login_service.login(usuario2_data, mesa.id)
        await db_session.commit()

        # Assert
        # Debe ser una sesión diferente
        assert response2.id_sesion_mesa != response1.id_sesion_mesa
        assert response2.token_sesion != response1.token_sesion

        # Verificar que la sesión original fue marcada como FINALIZADA
        await db_session.refresh(sesion_original)
        assert sesion_original.estado == EstadoSesionMesa.FINALIZADA
        assert sesion_original.fecha_fin is not None

        # Verificar que la nueva sesión está ACTIVA
        nueva_sesion = await sesion_repo.get_by_id(response2.id_sesion_mesa)
        assert nueva_sesion.estado == EstadoSesionMesa.ACTIVA

    async def test_login_sesion_activa_valida_reutiliza(self, db_session):
        """
        Test: Cuando hay una sesión activa y válida (no expirada),
        debe reutilizarla sin crear una nueva.
        """
        # Arrange
        mesa = MesaModel(numero=51, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_service = LoginService(db_session)

        # Primer login - crea sesión
        usuario1_data = LoginRequest(
            email="userA@correo.com",
            nombre="Usuario A"
        )
        response1 = await login_service.login(usuario1_data, mesa.id)
        await db_session.commit()

        # Act - Segundo login inmediato (sesión aún válida)
        usuario2_data = LoginRequest(
            email="userB@correo.com",
            nombre="Usuario B"
        )
        response2 = await login_service.login(usuario2_data, mesa.id)
        await db_session.commit()

        # Assert
        # Deben compartir la misma sesión
        assert response2.id_sesion_mesa == response1.id_sesion_mesa
        assert response2.token_sesion == response1.token_sesion
