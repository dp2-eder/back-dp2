from ulid import ULID
from datetime import date
from src.models.mesas.local_model import LocalModel
from src.core.enums.local_enums import TipoLocal


def test_local_model_creation():
    """
    Verifica que un objeto LocalModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id, codigo, nombre, direccion y tipo_local.

    PROCESO:
        - Crear un registro de LocalModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados durante.
    """
    local_id: str = str(ULID())
    local_codigo = "CEV-001"
    local_nombre = "La Cevichería del Centro"
    local_direccion = "Av. Principal 123"
    local_tipo = TipoLocal.CENTRAL

    local = LocalModel(
        id=local_id,
        codigo=local_codigo,
        nombre=local_nombre,
        direccion=local_direccion,
        tipo_local=local_tipo,
    )

    assert local.id == local_id
    assert local.codigo == local_codigo
    assert local.nombre == local_nombre
    assert local.direccion == local_direccion
    assert local.tipo_local == local_tipo


def test_local_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase LocalModel debe tener implementado el método to_dict().
        - Los atributos id, codigo, nombre, direccion, tipo_local y activo deben existir en el modelo.

    PROCESO:
        - Crear una instancia de LocalModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
    """
    local_id: str = str(ULID())
    local_codigo = "CEV-002"
    local_nombre = "La Cevichería de Miraflores"
    local_direccion = "Calle Los Olivos 456"
    local_distrito = "Miraflores"
    local_ciudad = "Lima"
    local_tipo = TipoLocal.SUCURSAL
    local_capacidad = 80
    local_fecha_apertura = date(2024, 1, 15)

    local = LocalModel(
        id=local_id,
        codigo=local_codigo,
        nombre=local_nombre,
        direccion=local_direccion,
        distrito=local_distrito,
        ciudad=local_ciudad,
        tipo_local=local_tipo,
        capacidad_total=local_capacidad,
        fecha_apertura=local_fecha_apertura,
    )

    dict_result = local.to_dict()

    assert "id" in dict_result
    assert "codigo" in dict_result
    assert "nombre" in dict_result
    assert "direccion" in dict_result
    assert "distrito" in dict_result
    assert "ciudad" in dict_result
    assert "tipo_local" in dict_result
    assert "capacidad_total" in dict_result
    assert "fecha_apertura" in dict_result

    assert dict_result["id"] == local_id
    assert dict_result["codigo"] == local_codigo
    assert dict_result["nombre"] == local_nombre
    assert dict_result["direccion"] == local_direccion
    assert dict_result["distrito"] == local_distrito
    assert dict_result["ciudad"] == local_ciudad
    assert dict_result["tipo_local"] == local_tipo.value
    assert dict_result["capacidad_total"] == local_capacidad
    assert dict_result["fecha_apertura"] == local_fecha_apertura.isoformat()
    assert dict_result["activo"] is None


def test_local_activo_default():
    """
    Verifica el comportamiento del valor predeterminado para el atributo activo.

    PRECONDICIONES:
        - La clase LocalModel debe tener un atributo activo con valor predeterminado.
        - La clase LocalModel debe aceptar la creación de instancias sin valor para activo.

    PROCESO:
        - Crear una instancia de LocalModel proporcionando solo los campos obligatorios.

    POSTCONDICIONES:
        - Los atributos con nullable=True deben ser None si no se proporcionan.
    """
    local = LocalModel(
        codigo="CEV-003",
        nombre="Test Local",
        direccion="Dirección Test",
        tipo_local=TipoLocal.CENTRAL,
    )

    # El default debería ser True según el modelo
    assert local.distrito is None
    assert local.ciudad is None
    assert local.telefono is None
    assert local.email is None
    assert local.capacidad_total is None
    assert local.fecha_apertura is None
    assert local.activo is None


def test_local_with_all_fields():
    """
    Verifica que un LocalModel se puede crear con todos los campos.

    PRECONDICIONES:
        - La clase LocalModel debe aceptar todos los campos definidos en el schema.

    PROCESO:
        - Crear una instancia de LocalModel con todos los campos proporcionados.

    POSTCONDICIONES:
        - Todos los campos deben tener los valores asignados correctamente.
    """
    local_id: str = str(ULID())
    local = LocalModel(
        id=local_id,
        codigo="CEV-004",
        nombre="La Cevichería Premium",
        direccion="Av. Larco 789",
        distrito="San Isidro",
        ciudad="Lima",
        telefono="01-2345678",
        email="contacto@cevicheria.com",
        tipo_local=TipoLocal.CENTRAL,
        capacidad_total=120,
        activo=True,
        fecha_apertura=date(2023, 5, 20),
    )

    assert local.id == local_id
    assert local.codigo == "CEV-004"
    assert local.nombre == "La Cevichería Premium"
    assert local.direccion == "Av. Larco 789"
    assert local.distrito == "San Isidro"
    assert local.ciudad == "Lima"
    assert local.telefono == "01-2345678"
    assert local.email == "contacto@cevicheria.com"
    assert local.tipo_local == TipoLocal.CENTRAL
    assert local.capacidad_total == 120
    assert local.activo is True
    assert local.fecha_apertura == date(2023, 5, 20)


def test_local_tipo_enum():
    """
    Verifica que el campo tipo_local maneja correctamente los valores del enum.

    PRECONDICIONES:
        - El enum TipoLocal debe estar definido con los valores CENTRAL y SUCURSAL.

    PROCESO:
        - Crear dos instancias de LocalModel, una con tipo CENTRAL y otra con SUCURSAL.

    POSTCONDICIONES:
        - Los valores del enum deben ser correctos en cada instancia.
    """
    local_central = LocalModel(
        codigo="CEV-005",
        nombre="Local Central",
        direccion="Dirección Central",
        tipo_local=TipoLocal.CENTRAL,
    )

    local_sucursal = LocalModel(
        codigo="CEV-006",
        nombre="Local Sucursal",
        direccion="Dirección Sucursal",
        tipo_local=TipoLocal.SUCURSAL,
    )

    assert local_central.tipo_local == TipoLocal.CENTRAL
    assert local_sucursal.tipo_local == TipoLocal.SUCURSAL
    assert str(local_central.tipo_local) == "CENTRAL"
    assert str(local_sucursal.tipo_local) == "SUCURSAL"
