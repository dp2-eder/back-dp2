from ulid import ULID
from src.models.auth.rol_model import RolModel
from src.models.mesas.mesa_model import MesaModel
from src.core.enums.mesa_enums import EstadoMesa

def test_mesa_model_creation():
    """
    Verifica que un objeto Mesa se crea correctamente.

    PRECONDICIONES:
        - Dado un id, numero, id_zona, capacidad.

    PROCESO:
        - Crear un registro de Mesa con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados durante la creación.
    """
    mesa_id: str = str(ULID())
    mesa_numero = 101
    mesa_capacidad = 4
    id_zona = str(ULID())
    mesa_estado = EstadoMesa.LIBRE

    mesa = MesaModel(
        id=mesa_id,
        numero=mesa_numero,
        capacidad=mesa_capacidad,
        id_zona=id_zona,
        estado=mesa_estado
    )

    assert mesa.id == mesa_id
    assert mesa.numero == mesa_numero
    assert mesa.capacidad == mesa_capacidad
    assert mesa.id_zona == id_zona
    assert mesa.estado == mesa_estado

   
def test_rol_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase MesaModel debe tener implementado el método to_dict().
        - Los atributos id, numero, capacidad, id_zona y estado deben existir en el modelo.

    PROCESO:
        - Crear una instancia de MesaModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
    """
    mesa_id: str = str(ULID())
    mesa_numero = 105
    mesa_capacidad = 6
    id_zona = str(ULID())
    mesa_estado = EstadoMesa.OCUPADA

    mesa = MesaModel(id=mesa_id, numero=mesa_numero, capacidad=mesa_capacidad,
                id_zona=id_zona, estado=mesa_estado)

    dict_result = mesa.to_dict()

    assert "id" in dict_result
    assert "numero" in dict_result
    assert "capacidad" in dict_result
    assert "id_zona" in dict_result
    assert "estado" in dict_result

    assert dict_result["id"] == mesa_id
    assert dict_result["numero"] == mesa_numero
    assert dict_result["capacidad"] == mesa_capacidad
    assert dict_result["id_zona"] == id_zona
    assert dict_result["estado"] == mesa_estado
    assert dict_result["activo"] is None
    


def test_mesa_activo_default():
    """
    Verifica el comportamiento del valor predeterminado para el atributo activo.

    PRECONDICIONES:
        - La clase MesaModel debe tener un atributo activo con valor predeterminado.
        - La clase MesaModel debe tener un atributo estado con valor predeterminado.
        - La clase MesaModel debe aceptar la creación de instancias sin valor para activo.

    PROCESO:
        - Crear una instancia de MesaModel proporcionando solo el nombre obligatorio.

    POSTCONDICIONES:
        - Los atributos con nullable=True deben ser None si no se proporcionan.
    """
    mesa = MesaModel(numero="101")

    # El default debería ser True según el modelo
    assert mesa.capacidad is None
    assert mesa.id_zona is None

