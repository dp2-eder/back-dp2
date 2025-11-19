from ulid import ULID
from src.models.mesas.zona_model import ZonaModel


def test_zona_model_creation():
    """
    Verifica que un objeto ZonaModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id, id_local, nombre y nivel.

    PROCESO:
        - Crear un registro de ZonaModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados.
    """
    zona_id: str = str(ULID())
    local_id: str = str(ULID())
    zona_nombre = "Terraza"
    zona_nivel = 0

    zona = ZonaModel(
        id=zona_id,
        id_local=local_id,
        nombre=zona_nombre,
        nivel=zona_nivel,
    )

    assert zona.id == zona_id
    assert zona.id_local == local_id
    assert zona.nombre == zona_nombre
    assert zona.nivel == zona_nivel


def test_zona_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase ZonaModel debe tener implementado el método to_dict().
        - Los atributos id, id_local, nombre, nivel y activo deben existir en el modelo.

    PROCESO:
        - Crear una instancia de ZonaModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
    """
    zona_id: str = str(ULID())
    local_id: str = str(ULID())
    zona_nombre = "Interior"
    zona_descripcion = "Zona interior del restaurante"
    zona_nivel = 0
    zona_capacidad = 50

    zona = ZonaModel(
        id=zona_id,
        id_local=local_id,
        nombre=zona_nombre,
        descripcion=zona_descripcion,
        nivel=zona_nivel,
        capacidad_maxima=zona_capacidad,
    )

    dict_result = zona.to_dict()

    assert "id" in dict_result
    assert "id_local" in dict_result
    assert "nombre" in dict_result
    assert "descripcion" in dict_result
    assert "nivel" in dict_result
    assert "capacidad_maxima" in dict_result

    assert dict_result["id"] == zona_id
    assert dict_result["id_local"] == local_id
    assert dict_result["nombre"] == zona_nombre
    assert dict_result["descripcion"] == zona_descripcion
    assert dict_result["nivel"] == zona_nivel
    assert dict_result["capacidad_maxima"] == zona_capacidad
    assert dict_result["activo"] is None


def test_zona_activo_default():
    """
    Verifica el comportamiento del valor predeterminado para el atributo activo.

    PRECONDICIONES:
        - La clase ZonaModel debe tener un atributo activo con valor predeterminado.
        - La clase ZonaModel debe aceptar la creación de instancias sin valor para activo.

    PROCESO:
        - Crear una instancia de ZonaModel proporcionando solo los campos obligatorios.

    POSTCONDICIONES:
        - Los atributos con nullable=True deben ser None si no se proporcionan.
    """
    local_id: str = str(ULID())
    zona = ZonaModel(
        id_local=local_id,
        nombre="VIP",
    )

    # Los atributos opcionales deben ser None si no se proporcionan
    assert zona.descripcion is None
    assert zona.capacidad_maxima is None
    # Los defaults solo se aplican al insertar en DB, no al crear instancia
    assert zona.activo is None
    assert zona.nivel is None


def test_zona_with_all_fields():
    """
    Verifica que un ZonaModel se puede crear con todos los campos.

    PRECONDICIONES:
        - La clase ZonaModel debe aceptar todos los campos definidos en el schema.

    PROCESO:
        - Crear una instancia de ZonaModel con todos los campos proporcionados.

    POSTCONDICIONES:
        - Todos los campos deben tener los valores asignados correctamente.
    """
    zona_id: str = str(ULID())
    local_id: str = str(ULID())
    zona = ZonaModel(
        id=zona_id,
        id_local=local_id,
        nombre="Terraza VIP",
        descripcion="Zona VIP en la terraza con vista panorámica",
        nivel=1,
        capacidad_maxima=30,
        activo=True,
    )

    assert zona.id == zona_id
    assert zona.id_local == local_id
    assert zona.nombre == "Terraza VIP"
    assert zona.descripcion == "Zona VIP en la terraza con vista panorámica"
    assert zona.nivel == 1
    assert zona.capacidad_maxima == 30
    assert zona.activo is True


def test_zona_nivel_values():
    """
    Verifica que el campo nivel acepta los valores esperados (0, 1, 2).

    PRECONDICIONES:
        - El campo nivel debe aceptar valores enteros.

    PROCESO:
        - Crear instancias de ZonaModel con diferentes niveles.

    POSTCONDICIONES:
        - Los valores del nivel deben ser correctos en cada instancia.
    """
    local_id: str = str(ULID())

    zona_principal = ZonaModel(
        id_local=local_id,
        nombre="Zona Principal",
        nivel=0,
    )

    zona_sub = ZonaModel(
        id_local=local_id,
        nombre="Sub-zona",
        nivel=1,
    )

    zona_sub_sub = ZonaModel(
        id_local=local_id,
        nombre="Sub-sub-zona",
        nivel=2,
    )

    assert zona_principal.nivel == 0
    assert zona_sub.nivel == 1
    assert zona_sub_sub.nivel == 2


def test_zona_foreign_key_field():
    """
    Verifica que el campo id_local (Foreign Key) se asigna correctamente.

    PRECONDICIONES:
        - El campo id_local debe aceptar valores string (ULID).

    PROCESO:
        - Crear una instancia de ZonaModel con un id_local específico.

    POSTCONDICIONES:
        - El id_local debe coincidir con el valor proporcionado.
    """
    local_id: str = str(ULID())
    zona = ZonaModel(
        id_local=local_id,
        nombre="Zona Test",
        nivel=0,
    )

    assert zona.id_local == local_id
    assert isinstance(zona.id_local, str)
