"""
Tests unitarios para el modelo UsuarioSesionMesaModel.
"""

import pytest
from datetime import datetime
from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel


class TestUsuarioSesionMesaModel:
    """Tests para el modelo UsuarioSesionMesaModel."""

    def test_create_usuario_sesion_mesa_model(self):
        """Test crear instancia de UsuarioSesionMesaModel."""
        # Arrange
        id_usuario = "01HXXX000000000000000000"
        id_sesion_mesa = "01HYYY000000000000000000"
        fecha_ingreso = datetime.now()

        # Act
        asociacion = UsuarioSesionMesaModel(
            id_usuario=id_usuario,
            id_sesion_mesa=id_sesion_mesa,
            fecha_ingreso=fecha_ingreso
        )

        # Assert
        assert asociacion.id is not None
        assert len(asociacion.id) == 26  # ULID tiene 26 caracteres
        assert asociacion.id_usuario == id_usuario
        assert asociacion.id_sesion_mesa == id_sesion_mesa
        assert asociacion.fecha_ingreso == fecha_ingreso

    def test_usuario_sesion_mesa_model_to_dict(self):
        """Test convertir UsuarioSesionMesaModel a diccionario."""
        # Arrange
        asociacion = UsuarioSesionMesaModel(
            id_usuario="01HXXX000000000000000000",
            id_sesion_mesa="01HYYY000000000000000000",
            fecha_ingreso=datetime.now()
        )

        # Act
        result = asociacion.to_dict()

        # Assert
        assert isinstance(result, dict)
        assert "id" in result
        assert "id_usuario" in result
        assert "id_sesion_mesa" in result
        assert "fecha_ingreso" in result
        assert result["id_usuario"] == "01HXXX000000000000000000"
        assert result["id_sesion_mesa"] == "01HYYY000000000000000000"

    def test_usuario_sesion_mesa_model_from_dict(self):
        """Test crear UsuarioSesionMesaModel desde diccionario."""
        # Arrange
        data = {
            "id": "01HZZZ000000000000000000",
            "id_usuario": "01HXXX000000000000000000",
            "id_sesion_mesa": "01HYYY000000000000000000",
            "fecha_ingreso": datetime.now()
        }

        # Act
        asociacion = UsuarioSesionMesaModel.from_dict(data)

        # Assert
        assert asociacion.id == data["id"]
        assert asociacion.id_usuario == data["id_usuario"]
        assert asociacion.id_sesion_mesa == data["id_sesion_mesa"]

    def test_usuario_sesion_mesa_model_update_from_dict(self):
        """Test actualizar UsuarioSesionMesaModel desde diccionario."""
        # Arrange
        asociacion = UsuarioSesionMesaModel(
            id_usuario="01HXXX000000000000000000",
            id_sesion_mesa="01HYYY000000000000000000"
        )
        nueva_fecha = datetime.now()
        update_data = {
            "fecha_ingreso": nueva_fecha
        }

        # Act
        asociacion.update_from_dict(update_data)

        # Assert
        assert asociacion.fecha_ingreso == nueva_fecha

    def test_usuario_sesion_mesa_model_repr(self):
        """Test representación en string de UsuarioSesionMesaModel."""
        # Arrange
        asociacion = UsuarioSesionMesaModel(
            id_usuario="01HXXX000000000000000000",
            id_sesion_mesa="01HYYY000000000000000000"
        )

        # Act
        repr_str = repr(asociacion)

        # Assert
        assert "UsuarioSesionMesa" in repr_str
        assert asociacion.id in repr_str
        assert "01HXXX000000000000000000" in repr_str
        assert "01HYYY000000000000000000" in repr_str
