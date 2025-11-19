"""
Excepciones personalizadas para operaciones de sesiones de mesa.
"""


class SesionMesaNotFoundError(Exception):
    """
    Excepción lanzada cuando una sesión de mesa no se encuentra en el sistema.

    Se utiliza cuando se intenta acceder, actualizar o eliminar una sesión
    que no existe en la base de datos.
    """

    pass


class SesionMesaValidationError(Exception):
    """
    Excepción lanzada cuando los datos de una sesión de mesa no cumplen
    con las validaciones requeridas.

    Ejemplos:
    - Usuario no existe
    - Mesa no existe
    - Intentar finalizar una sesión ya finalizada
    - Fecha de fin anterior a fecha de inicio
    """

    pass


class SesionMesaConflictError(Exception):
    """
    Excepción lanzada cuando hay un conflicto al crear o actualizar una
    sesión de mesa.

    Ejemplos:
    - Token de sesión duplicado
    - Violación de constraint de unicidad
    - Error de integridad referencial
    """

    pass


class SesionMesaInactivaError(Exception):
    """
    Excepción lanzada cuando se intenta usar una sesión de mesa que
    no está activa.

    Se utiliza cuando se intenta crear un pedido u otra operación
    que requiere una sesión activa, pero la sesión está finalizada.
    """

    pass
