"""
Excepciones personalizadas para el módulo de división de cuenta.

Define las excepciones específicas que pueden ocurrir durante las operaciones
relacionadas con divisiones de cuenta y sus detalles.
"""


class DivisionCuentaValidationError(Exception):
    """
    Excepción lanzada cuando falla la validación de datos de una división de cuenta.

    Se utiliza cuando los datos proporcionados para crear o actualizar una división
    no cumplen con las reglas de validación del negocio.

    Examples
    --------
    >>> raise DivisionCuentaValidationError("La cantidad de personas debe ser mayor a 0")
    """

    pass


class DivisionCuentaNotFoundError(Exception):
    """
    Excepción lanzada cuando no se encuentra una división de cuenta.

    Se utiliza cuando se intenta acceder, actualizar o eliminar una división
    que no existe en la base de datos.

    Examples
    --------
    >>> raise DivisionCuentaNotFoundError("No se encontró la división con ID 123")
    """

    pass


class DivisionCuentaConflictError(Exception):
    """
    Excepción lanzada cuando hay un conflicto al crear o actualizar una división.

    Se utiliza cuando se intenta crear una división que ya existe o cuando
    hay conflictos de integridad referencial.

    Examples
    --------
    >>> raise DivisionCuentaConflictError("El pedido ya tiene una división activa")
    """

    pass
