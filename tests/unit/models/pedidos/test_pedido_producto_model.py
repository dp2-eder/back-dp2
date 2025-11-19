from decimal import Decimal
from datetime import datetime
from ulid import ULID
from src.models.pedidos.pedido_producto_model import PedidoProductoModel


def test_pedido_producto_model_creation():
    """
    Verifica que un objeto PedidoProductoModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id, id_pedido, id_producto y otros campos.

    PROCESO:
        - Crear un registro de PedidoProductoModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados.
    """
    item_id: str = str(ULID())
    pedido_id: str = str(ULID())
    producto_id: str = str(ULID())

    item = PedidoProductoModel(
        id=item_id,
        id_pedido=pedido_id,
        id_producto=producto_id,
        cantidad=2,
        precio_unitario=Decimal("50.00"),
        precio_opciones=Decimal("5.00"),
        subtotal=Decimal("110.00"),
        notas_personalizacion="Sin cebolla",
    )

    assert item.id == item_id
    assert item.id_pedido == pedido_id
    assert item.id_producto == producto_id
    assert item.cantidad == 2
    assert item.precio_unitario == Decimal("50.00")
    assert item.precio_opciones == Decimal("5.00")
    assert item.subtotal == Decimal("110.00")
    assert item.notas_personalizacion == "Sin cebolla"


def test_pedido_producto_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase PedidoProductoModel debe tener implementado el método to_dict().

    PROCESO:
        - Crear una instancia de PedidoProductoModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
        - Los Decimales deben convertirse a float.
    """
    item_id: str = str(ULID())
    pedido_id: str = str(ULID())
    producto_id: str = str(ULID())

    item = PedidoProductoModel(
        id=item_id,
        id_pedido=pedido_id,
        id_producto=producto_id,
        cantidad=3,
        precio_unitario=Decimal("25.50"),
        precio_opciones=Decimal("3.50"),
        subtotal=Decimal("87.00"),
    )

    dict_result = item.to_dict()

    assert "id" in dict_result
    assert "id_pedido" in dict_result
    assert "id_producto" in dict_result
    assert "cantidad" in dict_result
    assert "subtotal" in dict_result

    assert dict_result["id"] == item_id
    assert dict_result["id_pedido"] == pedido_id
    assert dict_result["id_producto"] == producto_id
    assert dict_result["cantidad"] == 3
    assert dict_result["precio_unitario"] == 25.50  # Decimal convertido a float
    assert dict_result["precio_opciones"] == 3.50
    assert dict_result["subtotal"] == 87.00


def test_pedido_producto_calcular_subtotal():
    """
    Verifica que el método calcular_subtotal() funciona correctamente.

    PRECONDICIONES:
        - La clase PedidoProductoModel debe tener implementado calcular_subtotal().

    PROCESO:
        - Crear una instancia con cantidad y precios específicos.
        - Llamar al método calcular_subtotal().

    POSTCONDICIONES:
        - El subtotal debe ser: cantidad * (precio_unitario + precio_opciones).
    """
    item = PedidoProductoModel(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=4,
        precio_unitario=Decimal("15.00"),
        precio_opciones=Decimal("2.50"),
        subtotal=Decimal("0.00"),  # Valor temporal
    )

    subtotal_calculado = item.calcular_subtotal()

    # 4 * (15.00 + 2.50) = 4 * 17.50 = 70.00
    assert subtotal_calculado == Decimal("70.00")


def test_pedido_producto_cantidad_default():
    """
    Verifica el comportamiento del valor predeterminado para cantidad.

    PRECONDICIONES:
        - La clase PedidoProductoModel debe tener cantidad con default 1.

    PROCESO:
        - Crear una instancia especificando cantidad explícitamente.

    POSTCONDICIONES:
        - La cantidad debe ser la especificada.
    """
    item = PedidoProductoModel(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=1,
        precio_unitario=Decimal("10.00"),
        precio_opciones=Decimal("0.00"),
        subtotal=Decimal("10.00"),
    )

    assert item.cantidad == 1


def test_pedido_producto_precio_opciones_default():
    """
    Verifica el comportamiento del valor predeterminado para precio_opciones.

    PRECONDICIONES:
        - precio_opciones debe tener default 0.00.

    PROCESO:
        - Crear una instancia especificando precio_opciones explícitamente.

    POSTCONDICIONES:
        - precio_opciones debe ser el especificado.
    """
    item = PedidoProductoModel(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=1,
        precio_unitario=Decimal("10.00"),
        precio_opciones=Decimal("0.00"),
        subtotal=Decimal("10.00"),
    )

    assert item.precio_opciones == Decimal("0.00")


def test_pedido_producto_notas_nullable():
    """
    Verifica que notas_personalizacion es opcional (nullable).

    PRECONDICIONES:
        - notas_personalizacion debe ser nullable.

    PROCESO:
        - Crear una instancia sin especificar notas.

    POSTCONDICIONES:
        - notas_personalizacion debe ser None por defecto.
    """
    item = PedidoProductoModel(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=1,
        precio_unitario=Decimal("10.00"),
        precio_opciones=Decimal("0.00"),
        subtotal=Decimal("10.00"),
    )

    assert item.notas_personalizacion is None


def test_pedido_producto_repr():
    """
    Verifica que el método __repr__ funciona correctamente.

    PRECONDICIONES:
        - La clase PedidoProductoModel debe tener implementado __repr__.

    PROCESO:
        - Crear una instancia y obtener su representación en string.

    POSTCONDICIONES:
        - La representación debe incluir información clave del item.
    """
    pedido_id = str(ULID())
    producto_id = str(ULID())

    item = PedidoProductoModel(
        id=str(ULID()),
        id_pedido=pedido_id,
        id_producto=producto_id,
        cantidad=5,
        precio_unitario=Decimal("20.00"),
        precio_opciones=Decimal("5.00"),
        subtotal=Decimal("125.00"),
    )

    repr_str = repr(item)

    assert "PedidoProducto" in repr_str
    assert pedido_id in repr_str
    assert producto_id in repr_str
    assert "5" in repr_str  # cantidad
    assert "125.00" in repr_str  # subtotal
