"""
Módulo de modelo base.

Define las clases base para todos los modelos de la aplicación.
Implementa las mejores prácticas de SQLAlchemy 2.0 para definición de modelos.
"""

from typing import Any, Dict, Type, TypeVar
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy import inspect, String, event
from ulid import ULID

T = TypeVar("T", bound="BaseModel")


class BaseModel(DeclarativeBase):
    """Clase base para todos los modelos.

    Proporciona funcionalidades comunes y metadatos para todos los modelos
    de la aplicación. Implementa la estructura base siguiendo las mejores
    prácticas de SQLAlchemy 2.0.

    Attributes
    ----------
    id : str
        Identificador único ULID (Universally Unique Lexicographically Sortable Identifier).
        26 caracteres, ordenado cronológicamente.
    """

    # Metadata configurations can be added here
    __abstract__ = True

    # Definición de clave primaria usando ULID
    # ULID = timestamp-ordered, 26 chars
    id: Mapped[str] = mapped_column(
        String(26),  # 26 chars para ULID
        primary_key=True,
        default=lambda: str(ULID())
    )

    def __init__(self, **kwargs):
        """Inicializa el modelo generando automáticamente el ID si no se proporciona.

        En SQLAlchemy 2.0, los defaults de Python solo se ejecutan durante el INSERT
        a la base de datos. Para que el ID esté disponible inmediatamente después de
        crear la instancia (sin necesidad de flush), lo generamos en __init__.

        Parameters
        ----------
        **kwargs : dict
            Argumentos para inicializar el modelo.
        """
        # Auto-generar ID si no se proporciona
        if 'id' not in kwargs or kwargs.get('id') is None:
            kwargs['id'] = str(ULID())
        # Asignar todos los atributos usando setattr para evitar problemas con SQLAlchemy
        for key, value in kwargs.items():
            setattr(self, key, value)

    # Métodos comunes para todos los modelos
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia del modelo a un diccionario.

        Transforma todos los atributos del modelo en un diccionario para
        facilitar su serialización y uso en APIs.

        Returns
        -------
        Dict[str, Any]
            Diccionario con los nombres de columnas como claves y sus valores correspondientes.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Crea una instancia del modelo a partir de un diccionario.

        Parameters
        ----------
        data : Dict[str, Any]
            Diccionario con los datos para crear la instancia.

        Returns
        -------
        T
            Nueva instancia del modelo con los datos proporcionados.
        """
        return cls(
            **{k: v for k, v in data.items() if k in inspect(cls).columns.keys()}
        )

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza la instancia con datos de un diccionario.

        Parameters
        ----------
        data : Dict[str, Any]
            Diccionario con los datos para actualizar la instancia.
            El campo 'id' será automáticamente ignorado.
        """
        for key, value in data.items():
            if key != 'id' and hasattr(self, key):
                setattr(self, key, value)
