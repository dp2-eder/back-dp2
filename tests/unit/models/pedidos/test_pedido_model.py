from decimal import Decimal
from datetime import datetime
from ulid import ULID
from src.models.pedidos.pedido_model import PedidoModel
from src.core.enums.pedido_enums import EstadoPedido


def test_pedido_model_creation():
    """
    Verifica que un objeto PedidoModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id, id_mesa, numero_pedido y otros campos.

    PROCESO:
        - Crear un registro de PedidoModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados.
    """
    pedido_id: str = str(ULID())
    mesa_id: str = str(ULID())
    numero_pedido = "20251026-M001-001"

    pedido = PedidoModel(
        id=pedido_id,
        id_mesa=mesa_id,
        numero_pedido=numero_pedido,
        estado=EstadoPedido.PENDIENTE,
        subtotal=Decimal("100.00"),
        impuestos=Decimal("10.00"),
        descuentos=Decimal("5.00"),
        total=Decimal("105.00"),
        notas_cliente="Sin cebolla",
        notas_cocina="Urgente",
    )

    assert pedido.id == pedido_id
    assert pedido.id_mesa == mesa_id
    assert pedido.numero_pedido == numero_pedido
    assert pedido.estado == EstadoPedido.PENDIENTE
    assert pedido.subtotal == Decimal("100.00")
    assert pedido.impuestos == Decimal("10.00")
    assert pedido.descuentos == Decimal("5.00")
    assert pedido.total == Decimal("105.00")
    assert pedido.notas_cliente == "Sin cebolla"
    assert pedido.notas_cocina == "Urgente"


def test_pedido_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase PedidoModel debe tener implementado el método to_dict().
        - Los atributos id, id_mesa, numero_pedido, estado, etc. deben existir.

    PROCESO:
        - Crear una instancia de PedidoModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
        - Los Decimales deben convertirse a float.
        - Los Enums deben convertirse a string.
    """
    pedido_id: str = str(ULID())
    mesa_id: str = str(ULID())
    numero_pedido = "20251026-M001-001"

    pedido = PedidoModel(
        id=pedido_id,
        id_mesa=mesa_id,
        numero_pedido=numero_pedido,
        estado=EstadoPedido.CONFIRMADO,
        subtotal=Decimal("100.00"),
        total=Decimal("105.00"),
    )

    dict_result = pedido.to_dict()

    assert "id" in dict_result
    assert "id_mesa" in dict_result
    assert "numero_pedido" in dict_result
    assert "estado" in dict_result
    assert "subtotal" in dict_result
    assert "total" in dict_result

    assert dict_result["id"] == pedido_id
    assert dict_result["id_mesa"] == mesa_id
    assert dict_result["numero_pedido"] == numero_pedido
    assert dict_result["estado"] == "confirmado"  # Enum convertido a string
    assert dict_result["subtotal"] == 100.0  # Decimal convertido a float
    assert dict_result["total"] == 105.0


def test_pedido_estado_default():
    """
    Verifica el comportamiento del valor predeterminado para el atributo estado.

    PRECONDICIONES:
        - La clase PedidoModel debe tener un atributo estado con valor predeterminado PENDIENTE.

    PROCESO:
        - Crear una instancia de PedidoModel especificando el estado explícitamente.

    POSTCONDICIONES:
        - El estado debe ser PENDIENTE.
    """
    pedido = PedidoModel(
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
        estado=EstadoPedido.PENDIENTE,
    )

    assert pedido.estado == EstadoPedido.PENDIENTE


def test_pedido_monetary_defaults():
    """
    Verifica el comportamiento de los valores predeterminados para campos monetarios.

    PRECONDICIONES:
        - La clase PedidoModel debe tener valores predeterminados para subtotal y total.

    PROCESO:
        - Crear una instancia de PedidoModel especificando valores monetarios explícitamente.

    POSTCONDICIONES:
        - Los valores monetarios deben ser los especificados.
    """
    pedido = PedidoModel(
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
        subtotal=Decimal("0.00"),
        total=Decimal("0.00"),
    )

    assert pedido.subtotal == Decimal("0.00")
    assert pedido.total == Decimal("0.00")


def test_pedido_timestamps_nullable():
    """
    Verifica que los timestamps de estado son opcionales (nullable).

    PRECONDICIONES:
        - Los campos fecha_confirmado, fecha_en_preparacion, etc. deben ser nullable.

    PROCESO:
        - Crear una instancia de PedidoModel sin especificar timestamps.

    POSTCONDICIONES:
        - Los timestamps deben ser None por defecto.
    """
    pedido = PedidoModel(
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
    )

    assert pedido.fecha_confirmado is None
    assert pedido.fecha_en_preparacion is None
    assert pedido.fecha_listo is None
    assert pedido.fecha_entregado is None
    assert pedido.fecha_cancelado is None


def test_pedido_repr():
    """
    Verifica que el método __repr__ funciona correctamente.

    PRECONDICIONES:
        - La clase PedidoModel debe tener implementado __repr__.

    PROCESO:
        - Crear una instancia y obtener su representación en string.

    POSTCONDICIONES:
        - La representación debe incluir información clave del pedido.
    """
    pedido = PedidoModel(
        id=str(ULID()),
        id_mesa=str(ULID()),
        numero_pedido="20251026-M001-001",
        estado=EstadoPedido.LISTO,
        total=Decimal("150.00"),
    )

    repr_str = repr(pedido)

    assert "Pedido" in repr_str
    assert "20251026-M001-001" in repr_str
    assert "listo" in repr_str
    assert "150.00" in repr_str
