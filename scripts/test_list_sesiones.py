"""
Script para probar el endpoint de listar sesiones de mesa.

Ejecutar con:
    py -m scripts.test_list_sesiones
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# IMPORTANTE: Importar TODOS los modelos para que SQLAlchemy registre las relaciones
from src.models.menu.categoria_model import CategoriaModel
from src.models.menu.producto_model import ProductoModel
from src.models.menu.alergeno_model import AlergenoModel
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.models.pedidos.pedido_model import PedidoModel
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
from src.models.mesas.local_model import LocalModel
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel
from src.models.mesas.locales_categorias_model import LocalesCategoriasModel
from src.models.mesas.locales_productos_model import LocalesProductosModel
from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel
from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel
from src.models.auth.usuario_model import UsuarioModel
from src.models.auth.sesion_model import SesionModel
from src.models.auth.rol_model import RolModel
from src.models.pagos.division_cuenta_model import DivisionCuentaModel

from src.business_logic.mesas.sesion_mesa_service import SesionMesaService
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa


def get_database_url() -> str:
    """Obtiene la URL de la base de datos."""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url

    # SQLite por defecto
    return "sqlite+aiosqlite:///./instance/restaurante.db"


async def test_listar_sesiones():
    """Prueba el método de listar sesiones."""
    database_url = get_database_url()

    print("\n" + "="*70)
    print("🧪 PROBANDO ENDPOINT DE LISTAR SESIONES DE MESA")
    print("="*70)
    print(f"   Base de datos: {database_url}")
    print("="*70)

    # Crear engine y sesión
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        service = SesionMesaService(session)

        # TEST 1: Listar todas las sesiones
        print("\n📋 TEST 1: Listar TODAS las sesiones (sin filtros)")
        print("-" * 70)
        result = await service.get_sesiones_list(skip=0, limit=10)
        print(f"✅ Total de sesiones: {result.total}")
        print(f"   Página: {result.page}")
        print(f"   Límite: {result.limit}")
        print(f"   Sesiones retornadas: {len(result.sesiones)}")

        if result.sesiones:
            print(f"\n   Primeras 3 sesiones:")
            for i, sesion in enumerate(result.sesiones[:3], 1):
                print(f"   {i}. ID: {sesion.id}")
                print(f"      Mesa: {sesion.id_mesa}")
                print(f"      Token: {sesion.token_sesion}")
                print(f"      Estado: {sesion.estado.value}")
                print(f"      Fecha inicio: {sesion.fecha_inicio}")
                print()

        # TEST 2: Filtrar por estado ACTIVA
        print("\n📋 TEST 2: Filtrar por estado ACTIVA")
        print("-" * 70)
        result_activas = await service.get_sesiones_list(
            skip=0,
            limit=10,
            estado=EstadoSesionMesa.ACTIVA
        )
        print(f"✅ Total de sesiones ACTIVAS: {result_activas.total}")
        print(f"   Sesiones retornadas: {len(result_activas.sesiones)}")

        # TEST 3: Filtrar por estado CERRADA
        print("\n📋 TEST 3: Filtrar por estado CERRADA")
        print("-" * 70)
        result_cerradas = await service.get_sesiones_list(
            skip=0,
            limit=10,
            estado=EstadoSesionMesa.CERRADA
        )
        print(f"✅ Total de sesiones CERRADAS: {result_cerradas.total}")
        print(f"   Sesiones retornadas: {len(result_cerradas.sesiones)}")

        # TEST 4: Filtrar por id_mesa (si hay sesiones)
        if result.sesiones:
            id_mesa_ejemplo = result.sesiones[0].id_mesa
            print(f"\n📋 TEST 4: Filtrar por id_mesa = {id_mesa_ejemplo}")
            print("-" * 70)
            result_mesa = await service.get_sesiones_list(
                skip=0,
                limit=10,
                id_mesa=id_mesa_ejemplo
            )
            print(f"✅ Total de sesiones para esta mesa: {result_mesa.total}")
            print(f"   Sesiones retornadas: {len(result_mesa.sesiones)}")

        # TEST 5: Paginación
        print(f"\n📋 TEST 5: Paginación (página 1, límite 2)")
        print("-" * 70)
        result_page1 = await service.get_sesiones_list(skip=0, limit=2)
        print(f"✅ Página {result_page1.page}")
        print(f"   Total: {result_page1.total}")
        print(f"   Sesiones retornadas: {len(result_page1.sesiones)}")

        print(f"\n📋 TEST 6: Paginación (página 2, límite 2)")
        print("-" * 70)
        result_page2 = await service.get_sesiones_list(skip=2, limit=2)
        print(f"✅ Página {result_page2.page}")
        print(f"   Total: {result_page2.total}")
        print(f"   Sesiones retornadas: {len(result_page2.sesiones)}")

        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("="*70 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    # Configurar encoding UTF-8 para la consola de Windows
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    asyncio.run(test_listar_sesiones())
