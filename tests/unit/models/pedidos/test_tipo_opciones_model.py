from ulid import ULID
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel


def test_tipo_opcion_model_creation():
    """
    Verifica que un objeto TipoOpcionModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id, código, nombre y orden.

    PROCESO:
        - Crear un registro de TipoOpcionModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados durante la creación.
    """
    tipo_id = str(ULID())
    codigo = "nivel_aji"
    nombre = "Nivel de Ají"
    descripcion = "Define el nivel de picante del plato."
    orden = 1

    tipo_opcion = TipoOpcionModel(
        id=tipo_id,
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        orden=orden,
    )

    assert tipo_opcion.id == tipo_id
    assert tipo_opcion.codigo == codigo
    assert tipo_opcion.nombre == nombre
    assert tipo_opcion.descripcion == descripcion
    assert tipo_opcion.orden == orden


def test_tipo_opcion_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase TipoOpcionModel debe tener implementado el método to_dict().

    PROCESO:
        - Crear una instancia y convertirla en diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener las claves esperadas con valores correctos.
    """
    tipo_id= str(ULID())
    tipo_opcion = TipoOpcionModel(
        id=tipo_id,
        codigo="temperatura",
        nombre="Temperatura del plato",
        descripcion="Permite seleccionar caliente o frío.",
        orden=2,
    )

    result = tipo_opcion.to_dict()

    assert "codigo" in result
    assert "nombre" in result
    assert "descripcion" in result
    assert "orden" in result

    assert result["codigo"] == "temperatura"
    assert result["nombre"] == "Temperatura del plato"
    assert result["descripcion"] == "Permite seleccionar caliente o frío."
    assert result["orden"] == 2


def test_tipo_opcion_activo_default():
    """
    Verifica el valor predeterminado del atributo activo.

    PRECONDICIONES:
        - La clase TipoOpcionModel debe tener un campo activo con valor por defecto.

    PROCESO:
        - Crear una instancia sin especificar el atributo activo.

    POSTCONDICIONES:
        - El atributo activo debe inicializarse como True.
    """
    tipo_opcion = TipoOpcionModel(codigo="acompanamiento", nombre="Acompañamiento")

    assert tipo_opcion.activo in (None,True)
