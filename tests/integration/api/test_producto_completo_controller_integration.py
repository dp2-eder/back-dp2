"""
Pruebas de integración para el endpoint de actualización masiva de productos.
"""

import pytest
from ulid import ULID
from decimal import Decimal
from src.models.menu.producto_model import ProductoModel
from src.models.menu.categoria_model import CategoriaModel
from src.models.menu.alergeno_model import AlergenoModel
from src.repositories.menu.producto_repository import ProductoRepository
from src.core.enums.alergeno_enums import NivelRiesgo


@pytest.mark.asyncio
async def test_update_producto_completo_integration(async_client, db_session):
    """
    Prueba de integración para actualización masiva de producto.
    
    PRECONDICIONES:
        - El cliente asincrónico (async_client) debe estar configurado
        - La sesión de base de datos (db_session) debe estar disponible y en estado limpio
        - Los modelos necesarios deben ser accesibles
    
    PROCESO:
        - Crea categoría, alérgenos y producto en la base de datos.
        - Envía una solicitud PUT al endpoint con datos completos.
        - Verifica la respuesta y el estado en la base de datos.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos del producto deben actualizarse correctamente
        - El producto debe ser recuperable de la base de datos con los cambios
    """
    # Arrange - Create categoria
    categoria = CategoriaModel(
        id=str(ULID()),
        nombre="Pizzas Test",
        descripcion="Categoría de prueba",
        imagen_path="/images/pizzas.jpg",
        activo=True
    )
    db_session.add(categoria)
    await db_session.commit()

    # Create alergenos
    alergeno1 = AlergenoModel(
        id=str(ULID()),
        nombre="Gluten Test",
        descripcion="Alérgeno de prueba",
        icono="gluten.png",
        nivel_riesgo=NivelRiesgo.ALTO,
        activo=True
    )
    alergeno2 = AlergenoModel(
        id=str(ULID()),
        nombre="Lactosa Test",
        descripcion="Alérgeno de prueba",
        icono="lactosa.png",
        nivel_riesgo=NivelRiesgo.MEDIO,
        activo=True
    )
    db_session.add(alergeno1)
    db_session.add(alergeno2)
    await db_session.commit()

    # Create producto
    producto = ProductoModel(
        id=str(ULID()),
        nombre="Pizza Original",
        descripcion="Descripción original",
        precio_base=Decimal("10.00"),
        imagen_path="/images/pizza-original.jpg",
        imagen_alt_text="Pizza original",
        id_categoria=categoria.id,
        disponible=True,
        destacado=False
    )
    db_session.add(producto)
    await db_session.commit()

    # Prepare update data
    update_data = {
        "nombre": "Pizza Actualizada",
        "descripcion": "Descripción actualizada",
        "precio_base": "15.50",
        "imagen_path": "/images/pizza-actualizada.jpg",
        "imagen_alt_text": "Pizza actualizada",
        "id_categoria": categoria.id,
        "disponible": True,
        "destacado": True,
        "alergenos": [alergeno1.id, alergeno2.id],
        "secciones": [],
        "tipos_opciones": []
    }

    # Act
    response = await async_client.put(
        f"/api/v1/productos/{producto.id}/completo",
        json=update_data
    )

    # Debug: print response if not 200
    if response.status_code != 200:
        print(f"Error response: {response.status_code}")
        print(f"Response body: {response.json()}")
    
    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["nombre"] == "Pizza Actualizada"
    assert response_data["descripcion"] == "Descripción actualizada"
    assert response_data["precio_base"] == "15.50"
    assert response_data["destacado"] is True

    # Verify in database
    repo = ProductoRepository(db_session)
    producto_updated = await repo.get_by_id(producto.id)
    assert producto_updated is not None
    assert producto_updated.nombre == "Pizza Actualizada"
    assert producto_updated.destacado is True


@pytest.mark.asyncio
async def test_update_producto_completo_not_found_integration(async_client, db_session):
    """
    Prueba de integración para actualización de producto inexistente.
    
    PRECONDICIONES:
        - El cliente asincrónico (async_client) debe estar configurado
        - La sesión de base de datos (db_session) debe estar disponible
    
    PROCESO:
        - Genera un ID de producto que no existe.
        - Envía una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el producto
    """
    # Arrange
    producto_id_inexistente = str(ULID())
    categoria = CategoriaModel(
        id=str(ULID()),
        nombre="Categoría Test",
        descripcion="Descripción",
        imagen_path="/images/test.jpg",
        activo=True
    )
    db_session.add(categoria)
    await db_session.commit()

    update_data = {
        "nombre": "Producto Inexistente",
        "descripcion": "Descripción",
        "precio_base": "10.00",
        "imagen_path": "/images/test.jpg",
        "imagen_alt_text": "Test",
        "id_categoria": categoria.id,
        "disponible": True,
        "destacado": False,
        "alergenos": [],
        "secciones": [],
        "tipos_opciones": []
    }

    # Act
    response = await async_client.put(
        f"/api/v1/productos/{producto_id_inexistente}/completo",
        json=update_data
    )

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert "detail" in response_data
    assert "No se encontró el producto" in response_data["detail"]


@pytest.mark.asyncio
async def test_update_producto_completo_invalid_data_integration(async_client, db_session):
    """
    Prueba de integración para actualización con datos inválidos.
    
    PRECONDICIONES:
        - El cliente asincrónico (async_client) debe estar configurado
        - La sesión de base de datos (db_session) debe estar disponible
    
    PROCESO:
        - Crea un producto válido en la base de datos.
        - Envía una solicitud PUT con datos inválidos (precio negativo).
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 422 (Unprocessable Entity) por validación Pydantic
        - Los datos del producto no deben cambiar en la base de datos
    """
    # Arrange - Create categoria and producto
    categoria = CategoriaModel(
        id=str(ULID()),
        nombre="Categoría Test",
        descripcion="Descripción",
        imagen_path="/images/test.jpg",
        activo=True
    )
    db_session.add(categoria)
    await db_session.commit()

    producto = ProductoModel(
        id=str(ULID()),
        nombre="Pizza Test",
        descripcion="Descripción test",
        precio_base=Decimal("10.00"),
        imagen_path="/images/pizza.jpg",
        imagen_alt_text="Pizza",
        id_categoria=categoria.id,
        disponible=True,
        destacado=False
    )
    db_session.add(producto)
    await db_session.commit()

    # Invalid data (precio negativo)
    update_data = {
        "nombre": "Pizza Actualizada",
        "descripcion": "Descripción",
        "precio_base": "-5.00",  # Precio inválido
        "imagen_path": "/images/pizza.jpg",
        "imagen_alt_text": "Pizza",
        "id_categoria": categoria.id,
        "disponible": True,
        "destacado": False,
        "alergenos": [],
        "secciones": [],
        "tipos_opciones": []
    }

    # Act
    response = await async_client.put(
        f"/api/v1/productos/{producto.id}/completo",
        json=update_data
    )

    # Assert - Pydantic validation should reject this
    assert response.status_code == 422

    # Verify producto wasn't changed
    repo = ProductoRepository(db_session)
    producto_unchanged = await repo.get_by_id(producto.id)
    assert producto_unchanged.nombre == "Pizza Test"  # Original name
    assert producto_unchanged.precio_base == Decimal("10.00")  # Original price
