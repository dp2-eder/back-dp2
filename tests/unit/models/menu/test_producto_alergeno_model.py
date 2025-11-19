"""
Tests unitarios para el modelo ProductoAlergenoModel.

Verifica la correcta creación, conversión y manipulación de instancias
del modelo de relación producto-alérgeno.
"""

from ulid import ULID
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.core.enums.alergeno_enums import NivelPresencia

# Importar modelos relacionados para resolver dependencias de SQLAlchemy
from src.models.menu.producto_model import ProductoModel  # noqa: F401
from src.models.menu.alergeno_model import AlergenoModel  # noqa: F401


def test_producto_alergeno_model_creation():
    """
    Verifica que un objeto ProductoAlergenoModel se crea correctamente.

    PRECONDICIONES:
        - Dado un id_producto, id_alergeno y nivel_presencia.

    PROCESO:
        - Crear un registro de ProductoAlergenoModel con valores predefinidos.

    POSTCONDICIONES:
        - La instancia debe tener los valores exactos proporcionados.
        - El ID debe generarse automáticamente (ULID).
    """
    producto_id: str = str(ULID())
    alergeno_id: str = str(ULID())
    nivel = NivelPresencia.TRAZAS
    notas = "Puede contener trazas por contaminación cruzada"

    producto_alergeno = ProductoAlergenoModel(
        id_producto=producto_id,
        id_alergeno=alergeno_id,
        nivel_presencia=nivel,
        notas=notas
    )

    assert producto_alergeno.id is not None  # ID auto-generado
    assert len(producto_alergeno.id) == 26  # ULID tiene 26 caracteres
    assert producto_alergeno.id_producto == producto_id
    assert producto_alergeno.id_alergeno == alergeno_id
    assert producto_alergeno.nivel_presencia == nivel
    assert producto_alergeno.notas == notas


def test_producto_alergeno_to_dict():
    """
    Verifica que el método to_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase ProductoAlergenoModel debe tener implementado el método to_dict().
        - Los atributos id_producto, id_alergeno, nivel_presencia y activo deben existir.

    PROCESO:
        - Crear una instancia de ProductoAlergenoModel con valores específicos.
        - Llamar al método to_dict() para obtener un diccionario.

    POSTCONDICIONES:
        - El diccionario debe contener todas las claves esperadas.
        - Los valores deben coincidir con los de la instancia original.
    """
    producto_id: str = str(ULID())
    alergeno_id: str = str(ULID())
    nivel = NivelPresencia.CONTIENE

    producto_alergeno = ProductoAlergenoModel(
        id_producto=producto_id,
        id_alergeno=alergeno_id,
        nivel_presencia=nivel,
        notas="Contiene gluten"
    )

    dict_result = producto_alergeno.to_dict()

    assert "id_producto" in dict_result
    assert "id_alergeno" in dict_result
    assert "nivel_presencia" in dict_result
    assert "notas" in dict_result
    assert "activo" in dict_result

    assert dict_result["id_producto"] == producto_id
    assert dict_result["id_alergeno"] == alergeno_id
    assert dict_result["nivel_presencia"] == nivel
    assert dict_result["notas"] == "Contiene gluten"
    assert dict_result["activo"] is None


def test_producto_alergeno_default_values():
    """
    Verifica el comportamiento de los valores predeterminados.

    PRECONDICIONES:
        - La clase ProductoAlergenoModel debe tener valores predeterminados.
        - Debe aceptar la creación con solo las claves primarias.

    PROCESO:
        - Crear una instancia proporcionando solo id_producto e id_alergeno.

    POSTCONDICIONES:
        - nivel_presencia debe ser None en memoria (se asigna en DB).
        - notas debe ser None si no se proporciona.
        - activo debe ser None en memoria (True después de commit en DB).
    """
    producto_id: str = str(ULID())
    alergeno_id: str = str(ULID())

    producto_alergeno = ProductoAlergenoModel(
        id_producto=producto_id,
        id_alergeno=alergeno_id
    )

    # Verificar valores - None en memoria, valores por defecto se asignan en DB
    assert producto_alergeno.nivel_presencia is None  # Será CONTIENE en DB
    assert producto_alergeno.notas is None
    assert producto_alergeno.activo is None  # Será True en DB


def test_producto_alergeno_update_from_dict():
    """
    Verifica que el método update_from_dict() funciona correctamente.

    PRECONDICIONES:
        - La clase ProductoAlergenoModel debe tener implementado update_from_dict().
        - Las claves primarias (id_producto, id_alergeno) NO deben ser modificables.

    PROCESO:
        - Crear una instancia de ProductoAlergenoModel.
        - Actualizar con un diccionario que incluye cambios válidos.

    POSTCONDICIONES:
        - Los atributos modificables deben actualizarse.
        - Las claves primarias NO deben cambiar.
    """
    producto_id: str = str(ULID())
    alergeno_id: str = str(ULID())
    nuevo_producto_id: str = str(ULID())

    producto_alergeno = ProductoAlergenoModel(
        id_producto=producto_id,
        id_alergeno=alergeno_id,
        nivel_presencia=NivelPresencia.CONTIENE,
        notas="Original"
    )

    # Intentar actualizar (las claves primarias deben ignorarse)
    producto_alergeno.update_from_dict({
        "id_producto": nuevo_producto_id,  # Debe ser ignorado
        "nivel_presencia": NivelPresencia.TRAZAS,
        "notas": "Actualizado",
        "activo": False
    })

    # Las claves primarias NO deben cambiar
    assert producto_alergeno.id_producto == producto_id
    assert producto_alergeno.id_alergeno == alergeno_id

    # Los demás campos sí deben actualizarse
    assert producto_alergeno.nivel_presencia == NivelPresencia.TRAZAS
    assert producto_alergeno.notas == "Actualizado"
    assert producto_alergeno.activo is False
