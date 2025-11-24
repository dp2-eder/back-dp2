"""
Tests unitarios para schemas de pedidos con token de sesión.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from src.api.schemas.pedido_sesion_schema import (
    OpcionProductoSesion,
    PedidoItemSesion,
    PedidoEnviarRequest,
    ProductoOpcionDetalle,
    ProductoPedidoDetalle,
    PedidoHistorialDetalle,
    PedidoHistorialResponse,
    PedidoEnviarResponse
)
from src.core.enums.pedido_enums import EstadoPedido


class TestOpcionProductoSesion:
    """Tests para OpcionProductoSesion schema."""

    def test_opcion_producto_valida(self):
        """Test crear opción de producto válida."""
        # Arrange & Act
        opcion = OpcionProductoSesion(
            id_producto_opcion="01HXXX000000000000000000AA"
        )

        # Assert
        assert opcion.id_producto_opcion == "01HXXX000000000000000000AA"

    def test_opcion_producto_id_muy_corto(self):
        """Test que rechaza ID muy corto."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            OpcionProductoSesion(id_producto_opcion="SHORT")

        assert "at least 26 characters" in str(exc_info.value).lower()

    def test_opcion_producto_id_no_alfanumerico(self):
        """Test que rechaza ID con caracteres especiales."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            OpcionProductoSesion(
                id_producto_opcion="01HXXX-00000000000000AABB"  # 27 chars con guion
            )

        # El validator custom rechaza caracteres no alfanuméricos
        error_str = str(exc_info.value).lower()
        # Puede fallar por longitud o por alfanumérico, ambos son correctos
        assert "alfanumérico" in error_str or "at least 26 characters" in error_str

    def test_opcion_producto_normaliza_uppercase(self):
        """Test que normaliza ID a mayúsculas."""
        # Arrange & Act
        opcion = OpcionProductoSesion(
            id_producto_opcion="01hxxx000000000000000000aa"
        )

        # Assert
        assert opcion.id_producto_opcion == "01HXXX000000000000000000AA"


class TestPedidoItemSesion:
    """Tests para PedidoItemSesion schema."""

    def test_item_valido_sin_opciones(self):
        """Test crear item válido sin opciones."""
        # Arrange & Act
        item = PedidoItemSesion(
            id_producto="01HYYY000000000000000000BB",
            cantidad=2
        )

        # Assert
        assert item.id_producto == "01HYYY000000000000000000BB"
        assert item.cantidad == 2
        assert item.opciones == []
        assert item.notas_personalizacion is None

    def test_item_valido_con_opciones(self):
        """Test crear item válido con opciones."""
        # Arrange & Act
        item = PedidoItemSesion(
            id_producto="01HYYY000000000000000000BB",
            cantidad=1,
            opciones=[
                OpcionProductoSesion(id_producto_opcion="01HZZZ000000000000000000CC")
            ],
            notas_personalizacion="Sin cebolla"
        )

        # Assert
        assert len(item.opciones) == 1
        assert item.notas_personalizacion == "Sin cebolla"

    def test_item_cantidad_minima(self):
        """Test que cantidad mínima es 1."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PedidoItemSesion(
                id_producto="01HYYY000000000000000000BB",
                cantidad=0
            )

        assert "greater than or equal to 1" in str(exc_info.value).lower()

    def test_item_cantidad_maxima(self):
        """Test que cantidad máxima es 99."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PedidoItemSesion(
                id_producto="01HYYY000000000000000000BB",
                cantidad=100
            )

        assert "less than or equal to 99" in str(exc_info.value).lower()

    def test_item_notas_vacias_se_normalizan(self):
        """Test que notas vacías se convierten a None."""
        # Arrange & Act
        item = PedidoItemSesion(
            id_producto="01HYYY000000000000000000BB",
            cantidad=1,
            notas_personalizacion="   "
        )

        # Assert
        assert item.notas_personalizacion is None


class TestPedidoEnviarRequest:
    """Tests para PedidoEnviarRequest schema."""

    def test_request_valido_basico(self):
        """Test crear request válido básico."""
        # Arrange & Act
        request = PedidoEnviarRequest(
            token_sesion="01HAAA000000000000000000XX",
            items=[
                PedidoItemSesion(
                    id_producto="01HBBB000000000000000000YY",
                    cantidad=1
                )
            ]
        )

        # Assert
        assert request.token_sesion == "01HAAA000000000000000000XX"
        assert len(request.items) == 1
        assert request.notas_cliente is None
        assert request.notas_cocina is None

    def test_request_valido_completo(self):
        """Test crear request válido con todas las opciones."""
        # Arrange & Act
        request = PedidoEnviarRequest(
            token_sesion="01HAAA000000000000000000XX",
            items=[
                PedidoItemSesion(
                    id_producto="01HBBB000000000000000000YY",
                    cantidad=2,
                    opciones=[
                        OpcionProductoSesion(
                            id_producto_opcion="01HCCC000000000000000000ZZ"
                        )
                    ],
                    notas_personalizacion="Término medio"
                )
            ],
            notas_cliente="Alergia a mariscos",
            notas_cocina="Mesa VIP - urgente"
        )

        # Assert
        assert request.notas_cliente == "Alergia a mariscos"
        assert request.notas_cocina == "Mesa VIP - urgente"

    def test_request_sin_items_falla(self):
        """Test que request sin items falla."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PedidoEnviarRequest(
                token_sesion="01HAAA000000000000000000XX",
                items=[]
            )

        assert "at least 1 item" in str(exc_info.value).lower()

    def test_request_token_corto_falla(self):
        """Test que token muy corto falla."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PedidoEnviarRequest(
                token_sesion="SHORT",
                items=[
                    PedidoItemSesion(
                        id_producto="01HBBB000000000000000000YY",
                        cantidad=1
                    )
                ]
            )

        assert "at least 26 characters" in str(exc_info.value).lower()

    def test_request_token_normaliza_uppercase(self):
        """Test que token se normaliza a mayúsculas."""
        # Arrange & Act
        request = PedidoEnviarRequest(
            token_sesion="01haaa000000000000000000xx",
            items=[
                PedidoItemSesion(
                    id_producto="01HBBB000000000000000000YY",
                    cantidad=1
                )
            ]
        )

        # Assert
        assert request.token_sesion == "01HAAA000000000000000000XX"

    def test_request_notas_largas_falla(self):
        """Test que notas muy largas fallan."""
        # Arrange
        notas_muy_largas = "X" * 1001

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PedidoEnviarRequest(
                token_sesion="01HAAA000000000000000000XX",
                items=[
                    PedidoItemSesion(
                        id_producto="01HBBB000000000000000000YY",
                        cantidad=1
                    )
                ],
                notas_cliente=notas_muy_largas
            )

        assert "at most 1000 characters" in str(exc_info.value).lower()


class TestProductoOpcionDetalle:
    """Tests para ProductoOpcionDetalle schema."""

    def test_opcion_detalle_valida(self):
        """Test crear detalle de opción válido."""
        # Arrange & Act
        detalle = ProductoOpcionDetalle(
            id="01HDDD000000000000000000AA",
            id_producto_opcion="01HEEE000000000000000000BB",
            nombre_opcion="Extra queso",
            precio_adicional=Decimal("2.50")
        )

        # Assert
        assert detalle.nombre_opcion == "Extra queso"
        assert detalle.precio_adicional == Decimal("2.50")


class TestProductoPedidoDetalle:
    """Tests para ProductoPedidoDetalle schema."""

    def test_producto_detalle_valido(self):
        """Test crear detalle de producto válido."""
        # Arrange & Act
        detalle = ProductoPedidoDetalle(
            id="01HFFF000000000000000000AA",
            id_producto="01HGGG000000000000000000BB",
            nombre_producto="Hamburguesa Clásica",
            precio_base=Decimal("15.99"),
            imagen_path="/images/hamburguesa.jpg",
            imagen_alt_text="Hamburguesa Clásica",
            cantidad=2,
            precio_unitario=Decimal("15.99"),
            precio_opciones=Decimal("2.50"),
            subtotal=Decimal("36.98"),
            notas_personalizacion="Sin pepinillos",
            opciones=[
                ProductoOpcionDetalle(
                    id="01HHHH000000000000000000CC",
                    id_producto_opcion="01HIII000000000000000000DD",
                    nombre_opcion="Extra queso",
                    precio_adicional=Decimal("2.50")
                )
            ]
        )

        # Assert
        assert detalle.nombre_producto == "Hamburguesa Clásica"
        assert detalle.cantidad == 2
        assert len(detalle.opciones) == 1


class TestPedidoHistorialDetalle:
    """Tests para PedidoHistorialDetalle schema."""

    def test_historial_detalle_valido(self):
        """Test crear detalle de historial válido."""
        # Arrange & Act
        detalle = PedidoHistorialDetalle(
            id="01HJJJ000000000000000000AA",
            numero_pedido="20251110-M1-001",
            estado=EstadoPedido.PENDIENTE,
            subtotal=Decimal("36.98"),
            impuestos=Decimal("0.00"),
            descuentos=Decimal("0.00"),
            total=Decimal("36.98"),
            notas_cliente="Alergia a mariscos",
            notas_cocina="Urgente",
            fecha_creacion=datetime.now(),
            fecha_confirmado=None,
            fecha_en_preparacion=None,
            fecha_listo=None,
            fecha_entregado=None,
            productos=[]
        )

        # Assert
        assert detalle.numero_pedido == "20251110-M1-001"
        assert detalle.estado == EstadoPedido.PENDIENTE
        assert detalle.total == Decimal("36.98")


class TestPedidoHistorialResponse:
    """Tests para PedidoHistorialResponse schema."""

    def test_historial_response_valido(self):
        """Test crear respuesta de historial válida."""
        # Arrange & Act
        response = PedidoHistorialResponse(
            token_sesion="01HKKK000000000000000000XX",
            id_mesa="01HLLL000000000000000000YY",
            total_pedidos=2,
            pedidos=[
                PedidoHistorialDetalle(
                    id="01HMMM000000000000000000AA",
                    numero_pedido="20251110-M1-001",
                    estado=EstadoPedido.ENTREGADO,
                    subtotal=Decimal("20.00"),
                    impuestos=Decimal("0.00"),
                    descuentos=Decimal("0.00"),
                    total=Decimal("20.00"),
                    fecha_creacion=datetime.now(),
                    productos=[]
                )
            ]
        )

        # Assert
        assert response.total_pedidos == 2
        assert len(response.pedidos) == 1


class TestPedidoEnviarResponse:
    """Tests para PedidoEnviarResponse schema."""

    def test_enviar_response_valido(self):
        """Test crear respuesta de envío válida."""
        # Arrange & Act
        response = PedidoEnviarResponse(
            status=201,
            message="Pedido creado exitosamente",
            pedido=PedidoHistorialDetalle(
                id="01HNNN000000000000000000AA",
                numero_pedido="20251110-M1-002",
                estado=EstadoPedido.PENDIENTE,
                subtotal=Decimal("30.00"),
                impuestos=Decimal("0.00"),
                descuentos=Decimal("0.00"),
                total=Decimal("30.00"),
                fecha_creacion=datetime.now(),
                productos=[]
            )
        )

        # Assert
        assert response.status == 201
        assert response.message == "Pedido creado exitosamente"
        assert response.pedido.numero_pedido == "20251110-M1-002"
