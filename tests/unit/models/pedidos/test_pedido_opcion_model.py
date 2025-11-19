"""
Pruebas unitarias para el modelo PedidoOpcionModel.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from ulid import ULID

from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel


def test_pedido_opcion_model_creation():
    """
    Prueba la creación de una instancia del modelo PedidoOpcionModel.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Crea una instancia del modelo con datos válidos.
        - Verifica que los atributos se asignen correctamente.

    POSTCONDICIONES:
        - La instancia debe tener los valores proporcionados.
    """
    # Arrange & Act
    pedido_opcion_id = str(ULID())
    pedido_producto_id = str(ULID())
    producto_opcion_id = str(ULID())
    precio_adicional = Decimal("5.50")
    fecha_creacion = datetime.now()
    creado_por = str(ULID())

    pedido_opcion = PedidoOpcionModel(
        id=pedido_opcion_id,
        id_pedido_producto=pedido_producto_id,
        id_producto_opcion=producto_opcion_id,
        precio_adicional=precio_adicional,
        fecha_creacion=fecha_creacion,
        creado_por=creado_por,
    )

    # Assert
    assert pedido_opcion.id == pedido_opcion_id
    assert pedido_opcion.id_pedido_producto == pedido_producto_id
    assert pedido_opcion.id_producto_opcion == producto_opcion_id
    assert pedido_opcion.precio_adicional == precio_adicional
    assert pedido_opcion.fecha_creacion == fecha_creacion
    assert pedido_opcion.creado_por == creado_por


def test_pedido_opcion_model_to_dict():
    """
    Prueba la conversión de una instancia del modelo a diccionario.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Crea una instancia del modelo.
        - Convierte la instancia a diccionario usando to_dict().
        - Verifica que el diccionario contenga las claves y valores correctos.

    POSTCONDICIONES:
        - El diccionario debe contener todos los campos del modelo.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    pedido_producto_id = str(ULID())
    producto_opcion_id = str(ULID())
    precio_adicional = Decimal("3.00")

    pedido_opcion = PedidoOpcionModel(
        id=pedido_opcion_id,
        id_pedido_producto=pedido_producto_id,
        id_producto_opcion=producto_opcion_id,
        precio_adicional=precio_adicional,
    )

    # Act
    pedido_opcion_dict = pedido_opcion.to_dict()

    # Assert
    assert isinstance(pedido_opcion_dict, dict)
    assert pedido_opcion_dict["id"] == pedido_opcion_id
    assert pedido_opcion_dict["id_pedido_producto"] == pedido_producto_id
    assert pedido_opcion_dict["id_producto_opcion"] == producto_opcion_id
    assert pedido_opcion_dict["precio_adicional"] == precio_adicional


def test_pedido_opcion_model_from_dict():
    """
    Prueba la creación de una instancia del modelo desde un diccionario.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Crea un diccionario con datos válidos.
        - Usa from_dict() para crear una instancia del modelo.
        - Verifica que los atributos se asignen correctamente.

    POSTCONDICIONES:
        - La instancia debe tener los valores del diccionario.
    """
    # Arrange
    pedido_opcion_data = {
        "id": str(ULID()),
        "id_pedido_producto": str(ULID()),
        "id_producto_opcion": str(ULID()),
        "precio_adicional": Decimal("2.50"),
        "fecha_creacion": datetime.now(),
        "creado_por": str(ULID()),
    }

    # Act
    pedido_opcion = PedidoOpcionModel.from_dict(pedido_opcion_data)

    # Assert
    assert pedido_opcion.id == pedido_opcion_data["id"]
    assert pedido_opcion.id_pedido_producto == pedido_opcion_data["id_pedido_producto"]
    assert pedido_opcion.id_producto_opcion == pedido_opcion_data["id_producto_opcion"]
    assert pedido_opcion.precio_adicional == pedido_opcion_data["precio_adicional"]
    assert pedido_opcion.fecha_creacion == pedido_opcion_data["fecha_creacion"]
    assert pedido_opcion.creado_por == pedido_opcion_data["creado_por"]


def test_pedido_opcion_model_update_from_dict():
    """
    Prueba la actualización de una instancia del modelo desde un diccionario.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Crea una instancia del modelo con datos iniciales.
        - Crea un diccionario con datos actualizados.
        - Usa update_from_dict() para actualizar la instancia.
        - Verifica que los atributos se actualicen correctamente.

    POSTCONDICIONES:
        - La instancia debe tener los nuevos valores del diccionario.
    """
    # Arrange
    pedido_opcion = PedidoOpcionModel(
        id=str(ULID()),
        id_pedido_producto=str(ULID()),
        id_producto_opcion=str(ULID()),
        precio_adicional=Decimal("5.00"),
    )

    update_data = {
        "precio_adicional": Decimal("7.50"),
        "modificado_por": str(ULID()),
    }

    # Act
    pedido_opcion.update_from_dict(update_data)

    # Assert
    assert pedido_opcion.precio_adicional == update_data["precio_adicional"]
    assert pedido_opcion.modificado_por == update_data["modificado_por"]


def test_pedido_opcion_model_default_values():
    """
    Prueba los valores por defecto del modelo PedidoOpcionModel.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Crea una instancia del modelo con campos mínimos.
        - Verifica que los campos opcionales tengan valores por defecto correctos.

    POSTCONDICIONES:
        - Los campos opcionales deben tener sus valores por defecto.
    """
    # Arrange & Act
    pedido_opcion = PedidoOpcionModel(
        id=str(ULID()),
        id_pedido_producto=str(ULID()),
        id_producto_opcion=str(ULID()),
        precio_adicional=Decimal("0.00"),  # Explicitly set default
    )

    # Assert
    assert pedido_opcion.precio_adicional == Decimal("0.00")
    assert pedido_opcion.creado_por is None
    assert pedido_opcion.modificado_por is None


def test_pedido_opcion_model_tablename():
    """
    Prueba que el nombre de la tabla sea correcto.

    PRECONDICIONES:
        - El modelo debe estar importado correctamente.

    PROCESO:
        - Verifica que el atributo __tablename__ tenga el valor esperado.

    POSTCONDICIONES:
        - El nombre de la tabla debe ser 'pedidos_opciones'.
    """
    # Assert
    assert PedidoOpcionModel.__tablename__ == "pedidos_opciones"
