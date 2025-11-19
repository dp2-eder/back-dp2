"""
Pruebas unitarias para el modelo ProductoOpcionModel.

Este módulo contiene las pruebas unitarias para verificar el correcto funcionamiento
del modelo ProductoOpcionModel, incluyendo la creación, validación y métodos de utilidad.

PRECONDICIONES:
    - El módulo ProductoOpcionModel debe estar correctamente implementado.
    - SQLAlchemy y sus dependencias deben estar instaladas.
    - pytest debe estar disponible para ejecutar las pruebas.

PROCESO:
    - Crear instancias del modelo con diferentes configuraciones.
    - Verificar que los atributos se asignen correctamente.
    - Probar los métodos de utilidad (to_dict, from_dict, update_from_dict).

POSTCONDICIONES:
    - Todas las pruebas deben pasar satisfactoriamente.
    - El modelo debe funcionar según las especificaciones.
"""

from decimal import Decimal
from ulid import ULID
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel


def test_producto_opcion_creation():
    """
    Verifica que un objeto ProductoOpcionModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id, id_producto, id_tipo_opcion, nombre y otros campos.

    PROCESO:
        - Crear un registro de ProductoOpcionModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados.
    """
    opcion_id= str(ULID())
    producto_id= str(ULID())
    tipo_opcion_id= str(ULID())
    opcion_nombre = "Ají suave"
    precio_adicional = Decimal("2.50")

    opcion = ProductoOpcionModel(
        id=opcion_id,
        id_producto=producto_id,
        id_tipo_opcion=tipo_opcion_id,
        nombre=opcion_nombre,
        precio_adicional=precio_adicional,
        activo=True,
        orden=1,
    )

    assert opcion.id == opcion_id
    assert opcion.id_producto == producto_id
    assert opcion.id_tipo_opcion == tipo_opcion_id
    assert opcion.nombre == opcion_nombre
    assert opcion.precio_adicional == precio_adicional
    assert opcion.activo is True
    assert opcion.orden == 1


def test_producto_opcion_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase ProductoOpcionModel debe tener implementado el método to_dict().
        - Los atributos deben existir en el modelo.

    PROCESO:
        - Crear una instancia de ProductoOpcionModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
    """
    opcion_id= str(ULID())
    producto_id= str(ULID())
    tipo_opcion_id= str(ULID())
    opcion_nombre = "Sin ají"
    
    opcion = ProductoOpcionModel(
        id=opcion_id,
        id_producto=producto_id,
        id_tipo_opcion=tipo_opcion_id,
        nombre=opcion_nombre,
        precio_adicional=Decimal("0.00"),
    )

    dict_result = opcion.to_dict()

    assert "id" in dict_result
    assert "id_producto" in dict_result
    assert "id_tipo_opcion" in dict_result
    assert "nombre" in dict_result
    assert "precio_adicional" in dict_result
    assert "activo" in dict_result
    assert "orden" in dict_result

    assert dict_result["id"] == opcion_id
    assert dict_result["id_producto"] == producto_id
    assert dict_result["id_tipo_opcion"] == tipo_opcion_id
    assert dict_result["nombre"] == opcion_nombre
    assert dict_result["precio_adicional"] == Decimal("0.00")


def test_producto_opcion_defaults():
    """
    Verifica los valores predeterminados de los atributos.

    PRECONDICIONES:
        - La clase ProductoOpcionModel debe tener valores predeterminados definidos.

    PROCESO:
        - Crear una instancia de ProductoOpcionModel con solo los campos obligatorios.

    POSTCONDICIONES:
        - Los atributos con valores predeterminados deben tener los valores esperados.
    """
    producto_id= str(ULID())
    tipo_opcion_id= str(ULID())

    opcion = ProductoOpcionModel(
        id_producto=producto_id,
        id_tipo_opcion=tipo_opcion_id,
        nombre="Helada",
    )

    # Valores por defecto según el modelo
    assert opcion.precio_adicional is None  # Sin default en __init__
    assert opcion.activo is None  # Sin default en __init__
    assert opcion.orden is None  # Sin default en __init__


def test_producto_opcion_precio_decimal():
    """
    Verifica que el precio_adicional mantiene la precisión decimal correcta.

    PRECONDICIONES:
        - El campo precio_adicional debe ser de tipo DECIMAL(10, 2).

    PROCESO:
        - Crear una opción con un precio que tenga decimales.
        - Verificar que se mantiene la precisión.

    POSTCONDICIONES:
        - El precio debe mantener exactamente 2 decimales.
    """
    producto_id= str(ULID())
    tipo_opcion_id= str(ULID())

    opcion = ProductoOpcionModel(
        id_producto=producto_id,
        id_tipo_opcion=tipo_opcion_id,
        nombre="Con choclo",
        precio_adicional=Decimal("3.75"),
    )

    assert opcion.precio_adicional == Decimal("3.75")
    assert isinstance(opcion.precio_adicional, Decimal)


def test_producto_opcion_repr():
    """
    Verifica que el método __repr__ funciona correctamente.

    PRECONDICIONES:
        - La clase ProductoOpcionModel debe tener implementado __repr__.

    PROCESO:
        - Crear una instancia de ProductoOpcionModel.
        - Llamar a __repr__ (o str()).

    POSTCONDICIONES:
        - Debe retornar una representación en string legible.
    """
    producto_id= str(ULID())
    tipo_opcion_id= str(ULID())
    opcion_id= str(ULID())

    opcion = ProductoOpcionModel(
        id=opcion_id,
        id_producto=producto_id,
        id_tipo_opcion=tipo_opcion_id,
        nombre="Ají picante",
        precio_adicional=Decimal("1.50"),
        activo=True,
    )

    repr_str = repr(opcion)
    
    assert "ProductoOpcionModel" in repr_str
    assert str(opcion_id) in repr_str
    assert "Ají picante" in repr_str
    assert "1.50" in repr_str
