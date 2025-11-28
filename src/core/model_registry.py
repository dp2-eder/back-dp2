"""
Registro centralizado de modelos SQLAlchemy.

Este módulo asegura que todos los modelos estén registrados antes de que
los controladores sean importados, evitando errores de mapper no encontrado.
"""

# Auth models
from src.models.auth.usuario_model import UsuarioModel  # noqa: F401
from src.models.auth.sesion_model import SesionModel  # noqa: F401
from src.models.auth.admin_model import AdminModel  # noqa: F401
from src.models.auth.rol_model import RolModel  # noqa: F401

# Menu models
from src.models.menu.categoria_model import CategoriaModel  # noqa: F401
from src.models.menu.alergeno_model import AlergenoModel  # noqa: F401
from src.models.menu.producto_model import ProductoModel  # noqa: F401
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel  # noqa: F401

# Mesas models
from src.models.mesas.local_model import LocalModel  # noqa: F401
from src.models.mesas.zona_model import ZonaModel  # noqa: F401
from src.models.mesas.mesa_model import MesaModel  # noqa: F401
from src.models.mesas.sesion_mesa_model import SesionMesaModel  # noqa: F401
from src.models.mesas.locales_categorias_model import LocalesCategoriasModel  # noqa: F401
from src.models.mesas.locales_productos_model import LocalesProductosModel  # noqa: F401
from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel  # noqa: F401
from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel  # noqa: F401

# Pedidos models
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel  # noqa: F401
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel  # noqa: F401
from src.models.pedidos.pedido_model import PedidoModel  # noqa: F401
from src.models.pedidos.pedido_producto_model import PedidoProductoModel  # noqa: F401
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel  # noqa: F401

# Pagos models
from src.models.pagos.division_cuenta_model import DivisionCuentaModel  # noqa: F401
from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel  # noqa: F401


def register_all_models() -> None:
    """
    Registra todos los modelos SQLAlchemy.
    
    Esta función no hace nada en tiempo de ejecución, pero asegura que
    todos los modelos sean importados cuando este módulo se carga.
    """
    from src.models.auth.usuario_model import UsuarioModel  # noqa: F401
    from src.models.auth.sesion_model import SesionModel  # noqa: F401
    from src.models.auth.admin_model import AdminModel  # noqa: F401
    from src.models.auth.rol_model import RolModel  # noqa: F401

    # Menu models
    from src.models.menu.categoria_model import CategoriaModel  # noqa: F401
    from src.models.menu.alergeno_model import AlergenoModel  # noqa: F401
    from src.models.menu.producto_model import ProductoModel  # noqa: F401
    from src.models.menu.producto_alergeno_model import ProductoAlergenoModel  # noqa: F401

    # Mesas models
    from src.models.mesas.local_model import LocalModel  # noqa: F401
    from src.models.mesas.zona_model import ZonaModel  # noqa: F401
    from src.models.mesas.mesa_model import MesaModel  # noqa: F401
    from src.models.mesas.sesion_mesa_model import SesionMesaModel  # noqa: F401
    from src.models.mesas.locales_categorias_model import LocalesCategoriasModel  # noqa: F401
    from src.models.mesas.locales_productos_model import LocalesProductosModel  # noqa: F401
    from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel  # noqa: F401
    from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel  # noqa: F401

    # Pedidos models
    from src.models.pedidos.tipo_opciones_model import TipoOpcionModel  # noqa: F401
    from src.models.pedidos.producto_opcion_model import ProductoOpcionModel  # noqa: F401
    from src.models.pedidos.pedido_model import PedidoModel  # noqa: F401
    from src.models.pedidos.pedido_producto_model import PedidoProductoModel  # noqa: F401
    from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel  # noqa: F401

    # Pagos models
    from src.models.pagos.division_cuenta_model import DivisionCuentaModel  # noqa: F401
    from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel  # noqa: F401
    pass
