"""
Pruebas de integración para los endpoints de pedidos con token de sesión.
"""

import pytest
from decimal import Decimal
from ulid import ULID
from datetime import datetime

from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.local_model import LocalModel
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.models.auth.usuario_model import UsuarioModel
from src.models.menu.producto_model import ProductoModel
from src.models.menu.categoria_model import CategoriaModel
from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository
from src.repositories.pedidos.pedido_repository import PedidoRepository
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.core.enums.mesa_enums import EstadoMesa
from src.core.enums.local_enums import TipoLocal


@pytest.mark.asyncio
async def test_enviar_pedido_por_token_success_integration(async_client, db_session):
    """
    Prueba de integración para crear pedido con token de sesión exitosamente.

    PRECONDICIONES:
        - Cliente asincrónico y sesión de BD configurados
        - Modelos de mesa, usuario, producto y sesión disponibles

    PROCESO:
        - Crea local, zona, mesa, usuario, categoria, producto y sesión en BD
        - Envía solicitud POST a /api/v1/pedidos/enviar con token válido
        - Verifica respuesta y persistencia en BD

    POSTCONDICIONES:
        - Respuesta HTTP 201 con pedido creado
        - Pedido persistido con id_sesion_mesa correcto
        - Precios calculados desde BD
    """
    # Arrange - Create all dependencies
    # 1. Local
    local = LocalModel(
        id=str(ULID()),
        codigo="LOC001",
        nombre="Local Test",
        direccion="Test 123",
        telefono="123456789",
        tipo_local=TipoLocal.SUCURSAL,
        activo=True
    )
    db_session.add(local)

    # 2. Zona
    zona = ZonaModel(
        id=str(ULID()),
        nombre="Zona Test",
        id_local=local.id,
        activo=True
    )
    db_session.add(zona)

    # 3. Mesa
    mesa = MesaModel(
        id=str(ULID()),
        numero="001",
        capacidad=4,
        id_zona=zona.id,
        activo=True,
        estado=EstadoMesa.DISPONIBLE
    )
    db_session.add(mesa)

    # 4. Usuario
    usuario = UsuarioModel(
        id=str(ULID()),
        nombre="Test User",
        email="test@example.com",
        password_hash="hash123",
        id_rol=str(ULID()),
        activo=True
    )
    db_session.add(usuario)

    # 5. Sesión de mesa
    token = str(ULID())
    sesion = SesionMesaModel(
        id=str(ULID()),
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=token,
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now()
    )
    db_session.add(sesion)

    # 6. Categoría
    categoria = CategoriaModel(
        id=str(ULID()),
        nombre="Comida Test",
        descripcion="Test",
        activo=True
    )
    db_session.add(categoria)

    # 7. Producto
    producto = ProductoModel(
        id=str(ULID()),
        nombre="Hamburguesa Test",
        precio_base=Decimal("50.00"),
        imagen_path="/images/hamburguesa.jpg",
        imagen_alt_text="Hamburguesa Test",
        id_categoria=categoria.id,
        disponible=True
    )
    db_session.add(producto)

    await db_session.commit()

    # Act - Send POST request
    pedido_data = {
        "token_sesion": token,
        "items": [
            {
                "id_producto": producto.id,
                "cantidad": 2,
                "opciones": [],
                "notas_personalizacion": None
            }
        ],
        "notas_cliente": "Sin cebolla",
        "notas_cocina": None
    }

    response = await async_client.post("/api/v1/pedidos/enviar", json=pedido_data)

    # Assert
    assert response.status_code == 201
    response_data = response.json()

    assert response_data["status"] == 201
    assert response_data["message"] == "Pedido creado exitosamente"
    assert "pedido" in response_data

    pedido = response_data["pedido"]
    assert pedido["total"] == "100.00"  # 2 * 50.00
    assert pedido["subtotal"] == "100.00"
    assert pedido["notas_cliente"] == "Sin cebolla"
    assert len(pedido["productos"]) == 1
    assert pedido["productos"][0]["cantidad"] == 2
    assert pedido["productos"][0]["precio_unitario"] == "50.00"
    assert pedido["productos"][0]["precio_base"] == "50.00"
    assert pedido["productos"][0]["imagen_path"] == "/images/hamburguesa.jpg"
    assert pedido["productos"][0]["imagen_alt_text"] == "Hamburguesa Test"

    # Verify in database
    repo = PedidoRepository(db_session)
    pedidos, total = await repo.get_all(id_sesion_mesa=sesion.id)
    assert total == 1
    assert pedidos[0].id_sesion_mesa == sesion.id
    assert pedidos[0].id_mesa == mesa.id
    assert pedidos[0].total == Decimal("100.00")


@pytest.mark.asyncio
async def test_enviar_pedido_por_token_sesion_no_existe_integration(async_client):
    """
    Prueba de integración para crear pedido con token inexistente.

    POSTCONDICIONES:
        - Respuesta HTTP 400 con mensaje de error
    """
    # Arrange
    token_invalido = str(ULID())
    pedido_data = {
        "token_sesion": token_invalido,
        "items": [
            {
                "id_producto": str(ULID()),
                "cantidad": 1,
                "opciones": []
            }
        ]
    }

    # Act
    response = await async_client.post("/api/v1/pedidos/enviar", json=pedido_data)

    # Assert
    assert response.status_code == 400
    assert "No se encontró una sesión con el token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_enviar_pedido_por_token_sesion_no_activa_integration(async_client, db_session):
    """
    Prueba de integración para crear pedido con sesión finalizada.

    POSTCONDICIONES:
        - Respuesta HTTP 400 indicando que sesión no está activa
    """
    # Arrange - Create finalized session
    local = LocalModel(
        id=str(ULID()),
        codigo="LOC002",
        nombre="Local Test",
        direccion="Test 123",
        telefono="123456789",
        tipo_local=TipoLocal.SUCURSAL,
        activo=True
    )
    db_session.add(local)

    zona = ZonaModel(
        id=str(ULID()),
        nombre="Zona Test",
        id_local=local.id,
        activo=True
    )
    db_session.add(zona)

    mesa = MesaModel(
        id=str(ULID()),
        numero="001",
        capacidad=4,
        id_zona=zona.id,
        activo=True,
        estado=EstadoMesa.DISPONIBLE
    )
    db_session.add(mesa)

    usuario = UsuarioModel(
        id=str(ULID()),
        nombre="Test User",
        email="test@example.com",
        password_hash="hash123",
        id_rol=str(ULID()),
        activo=True
    )
    db_session.add(usuario)

    token = str(ULID())
    sesion = SesionMesaModel(
        id=str(ULID()),
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=token,
        estado=EstadoSesionMesa.FINALIZADA,  # ❌ No activa
        fecha_inicio=datetime.now(),
        fecha_fin=datetime.now()
    )
    db_session.add(sesion)
    await db_session.commit()

    pedido_data = {
        "token_sesion": token,
        "items": [
            {
                "id_producto": str(ULID()),
                "cantidad": 1,
                "opciones": []
            }
        ]
    }

    # Act
    response = await async_client.post("/api/v1/pedidos/enviar", json=pedido_data)

    # Assert
    assert response.status_code == 400
    assert "no está activa" in response.json()["detail"]


@pytest.mark.asyncio
async def test_obtener_historial_por_token_success_integration(async_client, db_session):
    """
    Prueba de integración para obtener historial de pedidos por token.

    POSTCONDICIONES:
        - Respuesta HTTP 200 con historial de pedidos
        - Incluye metadatos de sesión
    """
    # Arrange - Create session
    local = LocalModel(
        id=str(ULID()),
        codigo="LOC003",
        nombre="Local Test",
        direccion="Test 123",
        telefono="123456789",
        tipo_local=TipoLocal.SUCURSAL,
        activo=True
    )
    db_session.add(local)

    zona = ZonaModel(
        id=str(ULID()),
        nombre="Zona Test",
        id_local=local.id,
        activo=True
    )
    db_session.add(zona)

    mesa = MesaModel(
        id=str(ULID()),
        numero="001",
        capacidad=4,
        id_zona=zona.id,
        activo=True,
        estado=EstadoMesa.DISPONIBLE
    )
    db_session.add(mesa)

    usuario = UsuarioModel(
        id=str(ULID()),
        nombre="Test User",
        email="test@example.com",
        password_hash="hash123",
        id_rol=str(ULID()),
        activo=True
    )
    db_session.add(usuario)

    token = str(ULID())
    sesion = SesionMesaModel(
        id=str(ULID()),
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=token,
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now()
    )
    db_session.add(sesion)
    await db_session.commit()

    # Act
    response = await async_client.get(f"/api/v1/pedidos/historial/{token}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()

    assert response_data["token_sesion"] == token
    assert response_data["id_mesa"] == mesa.id
    assert response_data["total_pedidos"] == 0  # No pedidos aún
    assert response_data["pedidos"] == []


@pytest.mark.asyncio
async def test_obtener_historial_por_token_no_existe_integration(async_client):
    """
    Prueba de integración para obtener historial con token inexistente.

    POSTCONDICIONES:
        - Respuesta HTTP 400 con mensaje de error
    """
    # Arrange
    token_invalido = str(ULID())

    # Act
    response = await async_client.get(f"/api/v1/pedidos/historial/{token_invalido}")

    # Assert
    assert response.status_code == 400
    assert "No se encontró una sesión con el token" in response.json()["detail"]
