"""
Script para probar el flujo completo de pedidos con sesión compartida.

Flujo:
1. Obtener una mesa existente
2. Hacer login y obtener token de sesión
3. Listar productos disponibles
4. Crear un pedido con opciones (usando /pedidos/enviar)
5. Ver historial de pedidos (usando /pedidos/historial/{token})
6. Cerrar la sesión
7. Verificar que no se puede hacer más pedidos
8. Verificar que el historial retorna lista vacía

Ejecutar con:
    python -m scripts.test_flujo_pedido_sesion
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# IMPORTANTE: Importar TODOS los modelos para que SQLAlchemy registre las relaciones
# Modelos de menú
from src.models.menu.categoria_model import CategoriaModel
from src.models.menu.producto_model import ProductoModel
from src.models.menu.alergeno_model import AlergenoModel
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel

# Modelos de pedidos
from src.models.pedidos.pedido_model import PedidoModel
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel

# Modelos de mesas
from src.models.mesas.local_model import LocalModel
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel

# Modelos de tablas intermedias multi-local
from src.models.mesas.locales_categorias_model import LocalesCategoriasModel
from src.models.mesas.locales_productos_model import LocalesProductosModel
from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel
from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel

# Modelos de auth
from src.models.auth.usuario_model import UsuarioModel
from src.models.auth.sesion_model import SesionModel
from src.models.auth.rol_model import RolModel

# Modelos de pagos
from src.models.pagos.division_cuenta_model import DivisionCuentaModel

# Servicios
from src.business_logic.auth.login_service import LoginService
from src.business_logic.pedidos.pedido_service import PedidoService
from src.business_logic.mesas.sesion_mesa_service import SesionMesaService

# Schemas
from src.api.schemas.login_schema import LoginRequest
from src.api.schemas.pedido_sesion_schema import (
    PedidoEnviarRequest,
    PedidoItemSesion,
    OpcionProductoSesion,
)

# Excepciones
from src.business_logic.exceptions.pedido_exceptions import PedidoValidationError


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


class FlujoPedidoTester:
    """Tester para el flujo completo de pedidos con sesión."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.login_service = LoginService(session)
        self.pedido_service = PedidoService(session)
        self.sesion_service = SesionMesaService(session)

        self.mesa: Optional[MesaModel] = None
        self.token_sesion: str = ""  # Inicializar como string vacío
        self.id_sesion_mesa: str = ""
        self.id_usuario: str = ""
        self.productos = []
        self.pedido_creado = None

    async def paso_1_obtener_mesa(self):
        """Paso 1: Obtener una mesa existente."""
        print("\n" + "="*70)
        print("📍 PASO 1: OBTENER MESA EXISTENTE")
        print("="*70)

        result = await self.session.execute(
            select(MesaModel).limit(1)
        )
        self.mesa = result.scalars().first()

        if not self.mesa:
            raise RuntimeError(
                "❌ No hay mesas en la BD. "
                "Ejecuta primero el script de enriquecimiento o crea mesas."
            )

        print(f"✅ Mesa encontrada:")
        print(f"   ID: {self.mesa.id}")
        print(f"   Número: {self.mesa.numero}")
        print(f"   Capacidad: {self.mesa.capacidad}")
        print(f"   Estado: {self.mesa.estado.value}")

    async def paso_2_hacer_login(self):
        """Paso 2: Hacer login y obtener token de sesión."""
        print("\n" + "="*70)
        print("🔐 PASO 2: HACER LOGIN")
        print("="*70)

        # Validar que tenemos mesa
        if not self.mesa:
            raise RuntimeError("❌ No hay mesa disponible")

        login_data = LoginRequest(
            email="test@example.com",
            nombre="Usuario Test"
        )

        print(f"📧 Intentando login con:")
        print(f"   Email: {login_data.email}")
        print(f"   Nombre: {login_data.nombre}")

        response = await self.login_service.login(login_data, self.mesa.id)
        await self.session.commit()

        self.token_sesion = response.token_sesion
        self.id_sesion_mesa = response.id_sesion_mesa
        self.id_usuario = response.id_usuario

        print(f"\n✅ Login exitoso:")
        print(f"   ID Usuario: {self.id_usuario}")
        print(f"   ID Sesión Mesa: {self.id_sesion_mesa}")
        print(f"   Token Sesión: {self.token_sesion}")
        print(f"   Fecha Expiración: {response.fecha_expiracion}")

    async def paso_3_listar_productos(self):
        """Paso 3: Listar productos disponibles."""
        print("\n" + "="*70)
        print("🍽️  PASO 3: LISTAR PRODUCTOS DISPONIBLES")
        print("="*70)

        result = await self.session.execute(
            select(ProductoModel)
            .where(ProductoModel.disponible == True)
            .limit(10)
        )
        self.productos = result.scalars().all()

        if not self.productos:
            raise RuntimeError("❌ No hay productos disponibles en la BD.")

        print(f"✅ Se encontraron {len(self.productos)} productos disponibles")
        print("\n📋 Primeros 5 productos:")
        for i, producto in enumerate(self.productos[:5], 1):
            print(f"   {i}. {producto.nombre} - S/ {producto.precio_base}")

    async def paso_4_crear_pedido(self):
        """Paso 4: Crear un pedido con opciones."""
        print("\n" + "="*70)
        print("🛒 PASO 4: CREAR PEDIDO CON OPCIONES")
        print("="*70)

        # Validar que tenemos token
        if not self.token_sesion:
            raise RuntimeError("❌ No hay token de sesión disponible")

        # Seleccionar el primer producto
        producto_seleccionado = self.productos[0]
        print(f"📦 Producto seleccionado: {producto_seleccionado.nombre}")
        print(f"   Precio: S/ {producto_seleccionado.precio_base}")

        # Buscar opciones para este producto
        result = await self.session.execute(
            select(ProductoOpcionModel)
            .where(ProductoOpcionModel.id_producto == producto_seleccionado.id)
            .where(ProductoOpcionModel.activo == True)
            .limit(2)
        )
        opciones_disponibles = result.scalars().all()

        # Construir items del pedido
        opciones_seleccionadas = []
        if opciones_disponibles:
            print(f"\n⚙️  Opciones disponibles para este producto:")
            for opcion in opciones_disponibles:
                print(f"   - {opcion.nombre} (+S/ {opcion.precio_adicional})")
                opciones_seleccionadas.append(
                    OpcionProductoSesion(id_producto_opcion=opcion.id)
                )
        else:
            print(f"\n⚠️  Este producto no tiene opciones configuradas")

        # Crear el item del pedido
        item = PedidoItemSesion(
            id_producto=producto_seleccionado.id,
            cantidad=2,
            opciones=opciones_seleccionadas,
            notas_personalizacion="Sin cebolla, por favor"
        )

        # Crear el pedido
        pedido_data = PedidoEnviarRequest(
            token_sesion=self.token_sesion,
            items=[item],
            notas_cliente="Alérgico a mariscos",
            notas_cocina="Urgente para mesa VIP"
        )

        print(f"\n📝 Creando pedido...")
        print(f"   Token: {self.token_sesion}")
        print(f"   Cantidad de items: {len(pedido_data.items)}")
        print(f"   Cantidad del producto: {item.cantidad}")
        print(f"   Opciones seleccionadas: {len(opciones_seleccionadas)}")

        response = await self.pedido_service.enviar_pedido_por_token(pedido_data)
        await self.session.commit()

        self.pedido_creado = response.pedido

        print(f"\n✅ Pedido creado exitosamente:")
        print(f"   ID Pedido: {self.pedido_creado.id}")
        print(f"   Número Pedido: {self.pedido_creado.numero_pedido}")
        print(f"   Estado: {self.pedido_creado.estado.value}")
        print(f"   Subtotal: S/ {self.pedido_creado.subtotal}")
        print(f"   Impuestos: S/ {self.pedido_creado.impuestos}")
        print(f"   Descuentos: S/ {self.pedido_creado.descuentos}")
        print(f"   Total: S/ {self.pedido_creado.total}")
        print(f"   Productos: {len(self.pedido_creado.productos)}")

    async def paso_5_ver_historial(self):
        """Paso 5: Ver historial de pedidos."""
        print("\n" + "="*70)
        print("📜 PASO 5: VER HISTORIAL DE PEDIDOS")
        print("="*70)

        # Validar que tenemos token
        if not self.token_sesion:
            raise RuntimeError("❌ No hay token de sesión disponible")

        historial = await self.pedido_service.obtener_historial_por_token(self.token_sesion)

        print(f"✅ Historial obtenido:")
        print(f"   Token: {historial.token_sesion}")
        print(f"   ID Mesa: {historial.id_mesa}")
        print(f"   Estado Sesión: {historial.estado_sesion}")
        print(f"   Total Pedidos: {historial.total_pedidos}")

        if historial.mensaje:
            print(f"   ⚠️  Mensaje: {historial.mensaje}")

        if historial.pedidos:
            print(f"\n📋 Lista de pedidos:")
            for i, pedido in enumerate(historial.pedidos, 1):
                print(f"   {i}. Pedido #{pedido.numero_pedido}")
                print(f"      Estado: {pedido.estado.value}")
                print(f"      Total: S/ {pedido.total}")
                print(f"      Productos: {len(pedido.productos)}")
        else:
            print(f"\n⚠️  No hay pedidos en el historial")

    async def paso_6_cerrar_sesion(self):
        """Paso 6: Cerrar la sesión."""
        print("\n" + "="*70)
        print("🔒 PASO 6: CERRAR SESIÓN")
        print("="*70)

        # Validar que tenemos token
        if not self.token_sesion:
            raise RuntimeError("❌ No hay token de sesión disponible")

        print(f"🔐 Cerrando sesión con token: {self.token_sesion}")

        sesion_cerrada = await self.sesion_service.cerrar_sesion_por_token(self.token_sesion)
        await self.session.commit()

        print(f"\n✅ Sesión cerrada exitosamente:")
        print(f"   ID Sesión: {sesion_cerrada.id}")
        print(f"   Estado: {sesion_cerrada.estado.value}")
        print(f"   Token: {sesion_cerrada.token_sesion}")

    async def paso_7_verificar_no_pedido(self):
        """Paso 7: Verificar que no se puede hacer más pedidos."""
        print("\n" + "="*70)
        print("❌ PASO 7: VERIFICAR QUE NO SE PUEDE CREAR MÁS PEDIDOS")
        print("="*70)

        # Validar que tenemos token
        if not self.token_sesion:
            raise RuntimeError("❌ No hay token de sesión disponible")

        # Intentar crear otro pedido con la sesión cerrada
        producto = self.productos[0]
        item = PedidoItemSesion(
            id_producto=producto.id,
            cantidad=1,
            opciones=[],
            notas_personalizacion=None
        )

        pedido_data = PedidoEnviarRequest(
            token_sesion=self.token_sesion,
            items=[item],
            notas_cliente=None,
            notas_cocina=None
        )

        print(f"🚫 Intentando crear pedido con sesión cerrada...")

        try:
            await self.pedido_service.enviar_pedido_por_token(pedido_data)
            print(f"\n❌ ERROR: El pedido se creó cuando NO debería haberse creado")
            raise RuntimeError("El sistema permitió crear un pedido con sesión cerrada")
        except PedidoValidationError as e:
            print(f"\n✅ Correcto: El sistema rechazó el pedido")
            print(f"   Mensaje de error: {str(e)}")

            # Verificar que el mensaje contiene "no está activa"
            if "no está activa" in str(e).lower():
                print(f"   ✅ El mensaje contiene 'no está activa' como esperado")
            else:
                print(f"   ⚠️  ADVERTENCIA: El mensaje NO contiene 'no está activa'")

    async def paso_8_verificar_historial_vacio(self):
        """Paso 8: Verificar que el historial retorna lista vacía."""
        print("\n" + "="*70)
        print("📭 PASO 8: VERIFICAR HISTORIAL VACÍO TRAS CIERRE")
        print("="*70)

        # Validar que tenemos token
        if not self.token_sesion:
            raise RuntimeError("❌ No hay token de sesión disponible")

        print(f"📜 Consultando historial con sesión cerrada...")

        historial = await self.pedido_service.obtener_historial_por_token(self.token_sesion)

        print(f"\n📊 Resultado del historial:")
        print(f"   Estado Sesión: {historial.estado_sesion}")
        print(f"   Total Pedidos: {historial.total_pedidos}")
        print(f"   Cantidad de pedidos: {len(historial.pedidos)}")

        if historial.mensaje:
            print(f"   💬 Mensaje: {historial.mensaje}")

        # Verificar que está vacío
        if historial.total_pedidos == 0 and len(historial.pedidos) == 0:
            print(f"\n✅ Correcto: El historial retorna lista vacía")
        else:
            print(f"\n❌ ERROR: El historial NO está vacío")
            print(f"   Se esperaba: total_pedidos=0, pedidos=[]")
            print(f"   Se obtuvo: total_pedidos={historial.total_pedidos}, pedidos={len(historial.pedidos)}")
            raise RuntimeError("El historial debería estar vacío para sesiones cerradas")

    async def ejecutar_flujo_completo(self):
        """Ejecuta todos los pasos del flujo."""
        print("\n" + "="*70)
        print("🚀 INICIANDO PRUEBA DE FLUJO COMPLETO DE PEDIDOS CON SESIÓN")
        print("="*70)
        print("Este script probará:")
        print("  1. Obtener mesa existente")
        print("  2. Hacer login y obtener token")
        print("  3. Listar productos disponibles")
        print("  4. Crear pedido con opciones")
        print("  5. Ver historial de pedidos")
        print("  6. Cerrar la sesión")
        print("  7. Verificar que no se puede crear más pedidos")
        print("  8. Verificar que el historial retorna vacío")
        print("="*70)

        try:
            await self.paso_1_obtener_mesa()
            await self.paso_2_hacer_login()
            await self.paso_3_listar_productos()
            await self.paso_4_crear_pedido()
            await self.paso_5_ver_historial()
            await self.paso_6_cerrar_sesion()
            await self.paso_7_verificar_no_pedido()
            await self.paso_8_verificar_historial_vacio()

            print("\n" + "="*70)
            print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
            print("="*70)
            print("🎉 Todos los pasos del flujo se ejecutaron correctamente:")
            print("   ✅ Login con token de sesión")
            print("   ✅ Creación de pedido con opciones")
            print("   ✅ Consulta de historial (sesión activa)")
            print("   ✅ Cierre de sesión")
            print("   ✅ Rechazo de pedidos (sesión cerrada)")
            print("   ✅ Historial vacío (sesión cerrada)")
            print("="*70 + "\n")

        except Exception as e:
            print("\n" + "="*70)
            print("❌ ERROR EN LA PRUEBA")
            print("="*70)
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensaje: {str(e)}")
            print("="*70 + "\n")
            raise


async def main():
    """Función principal."""
    database_url = get_database_url()

    print("\n" + "="*70)
    print("⚙️  CONFIGURACIÓN DE BASE DE DATOS")
    print("="*70)
    print(f"   URL: {database_url}")
    print("="*70)

    # Crear engine y sesión
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        tester = FlujoPedidoTester(session)
        await tester.ejecutar_flujo_completo()

    await engine.dispose()


if __name__ == "__main__":
    # Configurar encoding UTF-8 para la consola de Windows
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    asyncio.run(main())
