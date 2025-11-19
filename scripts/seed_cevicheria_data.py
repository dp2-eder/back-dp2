"""
Script para poblar la base de datos con datos mock de una cevichería peruana.

Ejecutar con:
    python -m scripts.seed_cevicheria_data
"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal
import os

# ✅ AGREGAR ESTAS DOS LÍNEAS
from dotenv import load_dotenv
load_dotenv()  # Carga el .env ANTES de usar os.getenv()

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.database import BaseModel
# from src.models.auth.rol_model import RolModel  # ELIMINADO: Ya no se usa RolModel
from src.models.menu.categoria_model import CategoriaModel
from src.models.menu.alergeno_model import AlergenoModel
from src.models.menu.producto_model import ProductoModel
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
from src.core.enums.alergeno_enums import NivelPresencia


def get_database_url() -> str:
    """
    Obtiene la URL de la base de datos desde variables de entorno o usa SQLite por defecto.
    
    Returns:
        str: URL de conexión a la base de datos
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Fallback
        database_url = "sqlite+aiosqlite:///instance/restaurant.db"
    
    return database_url


class CevicheriaSeeder:
    """Clase para poblar la base de datos con datos de cevichería."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # self.roles = {}  # ELIMINADO: Ya no se usan roles
        self.categorias = {}
        self.alergenos = {}
        self.productos = {}
        self.tipos_opciones = {}
        self.productos_opciones = {}
    
    async def seed_all(self):
        """Ejecuta todos los seeders en orden."""
        print("🌊 Iniciando seed de datos para Cevichería...\n")

        # await self.seed_roles()  # ELIMINADO: Ya no se usan roles
        await self.seed_categorias()
        await self.seed_alergenos()
        await self.seed_productos()
        await self.seed_productos_alergenos()
        await self.seed_tipos_opciones()
        await self.seed_productos_opciones()

        print("\n✅ ¡Seed completado exitosamente!")
        # print(f"   - {len(self.roles)} roles")  # ELIMINADO
        print(f"   - {len(self.categorias)} categorías")
        print(f"   - {len(self.alergenos)} alérgenos")
        print(f"   - {len(self.productos)} productos")
        print(f"   - {len(self.tipos_opciones)} tipos de opciones")
        print(f"   - {len(self.productos_opciones)} opciones de productos")
    
    # MÉTODO ELIMINADO: seed_roles()
    # Ya no se crean roles porque RolModel fue eliminado del sistema.
    # El nuevo sistema de login simplificado no usa roles.
    
    async def seed_categorias(self):
        """Crea categorías de productos."""
        print("📂 Creando categorías...")
        
        categorias_data = [
            {
                "nombre": "Ceviches",
                "descripcion": "Ceviches frescos del día con pescados y mariscos selectos",
                "imagen_path": "https://drive.google.com/file/d/1ZaYA_c1ZGfl6tsPe80-fwSzpHR_LYzSZ/view?usp=sharing",
                "activo": True
            },
            {
                "nombre": "Tiraditos",
                "descripcion": "Finas láminas de pescado fresco con salsas especiales",
                "imagen_path": "https://drive.google.com/file/d/10xFfoYsezQRTC3EvLKm28BJGnImhAJjO/view?usp=sharing",
                "activo": True
            },
            {
                "nombre": "Chicharrones",
                "descripcion": "Chicharrones crujientes de pescado y mariscos",
                "imagen_path": "https://drive.google.com/file/d/1FYmm0IoKTx3tAgumxpZfSIx4GIrPtD4G/view?usp=sharing",
                "activo": True
            },
            {
                "nombre": "Arroces",
                "descripcion": "Arroces marinos con mariscos frescos",
                "imagen_path": "https://drive.google.com/file/d/14xM_kLEcGtsOORHEp5MCDMCJIGgzs45J/view?usp=sharing",
                "activo": True
            },
            {
                "nombre": "Causas",
                "descripcion": "Causas rellenas de diferentes mariscos",
                "imagen_path": "https://drive.google.com/file/d/1kRcHUgMqWTHDEX5XVUYNlGPTnkMOQRsa/view?usp=sharing",
                "activo": True
            },
            {
                "nombre": "Bebidas",
                "descripcion": "Bebidas refrescantes, chicha morada, limonada y más",
                "imagen_path": "https://drive.google.com/file/d/1AhNWmlJwuWb0XzXV8Zjs0xD2ZPHT6jzm/view?usp=sharing",
                "activo": True
            },
            {
                "nombre": "Postres",
                "descripcion": "Postres tradicionales peruanos",
                "imagen_path": "https://drive.google.com/file/d/1gxaT1PCMx1lQ-Hvcug9ujWr3RnVK3WPd/view?usp=sharing",
                "activo": True
            }
        ]
        
        for data in categorias_data:
            categoria = CategoriaModel(**data)
            self.session.add(categoria)
            self.categorias[data["nombre"]] = categoria
            print(f"   ✓ {data['nombre']}")
        
        await self.session.commit()
        print(f"   → {len(categorias_data)} categorías creadas\n")
    
    async def seed_alergenos(self):
        """Crea alérgenos comunes."""
        print("⚠️  Creando alérgenos...")
        
        alergenos_data = [
            {
                "nombre": "Mariscos",
                "descripcion": "Langostinos, camarones, pulpo, calamar, conchas negras",
                "activo": True
            },
            {
                "nombre": "Pescado",
                "descripcion": "Lenguado, corvina, mero, bonito, atún",
                "activo": True
            },
            {
                "nombre": "Moluscos",
                "descripcion": "Conchas de abanico, pulpo, calamar",
                "activo": True
            },
            {
                "nombre": "Gluten",
                "descripcion": "Presente en masas, panes y algunos aderezos",
                "activo": True
            },
            {
                "nombre": "Lácteos",
                "descripcion": "Leche, queso, crema de leche",
                "activo": True
            },
            {
                "nombre": "Ají",
                "descripcion": "Rocoto, ají amarillo, ají limo",
                "activo": True
            },
            {
                "nombre": "Soja",
                "descripcion": "Salsa de soja y derivados",
                "activo": True
            },
            {
                "nombre": "Frutos Secos",
                "descripcion": "Maní, nueces, almendras",
                "activo": True
            }
        ]
        
        for data in alergenos_data:
            alergeno = AlergenoModel(**data)
            self.session.add(alergeno)
            self.alergenos[data["nombre"]] = alergeno
            print(f"   ✓ {data['nombre']}")
        
        await self.session.commit()
        print(f"   → {len(alergenos_data)} alérgenos creados\n")
    
    async def seed_productos(self):
        """Crea productos de la cevichería."""
        print("🍽️  Creando productos...")
        
        # Refrescar categorías para obtener IDs
        for cat in self.categorias.values():
            await self.session.refresh(cat)
        
        productos_data = [
            # CEVICHES
            {
                "nombre": "Ceviche Clásico",
                "descripcion": "Pescado fresco del día marinado en limón, cebolla morada, ají limo y cilantro. Acompañado de camote, choclo y cancha",
                "precio_base": Decimal("25.00"),
                "id_categoria": self.categorias["Ceviches"].id,
                "imagen_path": "https://drive.google.com/file/d/14MotvG3-NJLZO5bUJjGqyMkOMMSzOZ7L/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Ceviche Mixto",
                "descripcion": "Combinación de pescado, pulpo, calamar y langostinos marinados en limón con rocoto molido",
                "precio_base": Decimal("35.00"),
                "id_categoria": self.categorias["Ceviches"].id,
                "imagen_path": "https://drive.google.com/file/d/18wtI2hmnm2mDhV73cU-ow6XJUUgzXVnP/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Ceviche de Conchas Negras",
                "descripcion": "Conchas negras frescas con su jugo natural, marinadas en limón y ají limo",
                "precio_base": Decimal("45.00"),
                "id_categoria": self.categorias["Ceviches"].id,
                "imagen_path": "https://drive.google.com/file/d/1qsrha511qKobIjyCV91PDmJxPcOz8tOd/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Ceviche de Pulpo",
                "descripcion": "Pulpo tierno marinado en limón con cebolla morada y ají amarillo",
                "precio_base": Decimal("38.00"),
                "id_categoria": self.categorias["Ceviches"].id,
                "imagen_path": "https://drive.google.com/file/d/1dIm4pjLo3E2g_Zop6rvNXc8OErAmHuBd/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            # TIRADITOS
            {
                "nombre": "Tiradito Clásico",
                "descripcion": "Finas láminas de pescado con salsa de ají amarillo, rocoto y limón",
                "precio_base": Decimal("28.00"),
                "id_categoria": self.categorias["Tiraditos"].id,
                "imagen_path": "https://drive.google.com/file/d/1gXlCGBSnduNLxla2WA1kDnMnci7WpJHh/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Tiradito Nikkei",
                "descripcion": "Láminas de pescado con salsa de ají amarillo, sillao y aceite de sésamo",
                "precio_base": Decimal("32.00"),
                "id_categoria": self.categorias["Tiraditos"].id,
                "imagen_path": "https://drive.google.com/file/d/1QNR6LydeY06cg_71gw376Iep3dZddvsI/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Tiradito de Atún",
                "descripcion": "Láminas de atún fresco con salsa de maracuyá y ají limo",
                "precio_base": Decimal("40.00"),
                "id_categoria": self.categorias["Tiraditos"].id,
                "imagen_path": "https://drive.google.com/file/d/1Nv1fxVvE4zoEzdnQ44hoAhfQnRKiI2ov/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            # CHICHARRONES
            {
                "nombre": "Chicharrón de Pescado",
                "descripcion": "Trozos de pescado empanizados y fritos, servido con yucas y sarsa criolla",
                "precio_base": Decimal("30.00"),
                "id_categoria": self.categorias["Chicharrones"].id,
                "imagen_path": "https://drive.google.com/file/d/1-7MmcqQ0cWRFJUj2uuiXhGHHzGOZseDn/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Chicharrón de Calamar",
                "descripcion": "Anillos de calamar fritos crujientes con salsa tártara",
                "precio_base": Decimal("32.00"),
                "id_categoria": self.categorias["Chicharrones"].id,
                "imagen_path": "https://drive.google.com/file/d/1i0KzBtnznRC71VMMT5ZUPnIbPky7vJYo/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Chicharrón Mixto",
                "descripcion": "Combinación de pescado, calamar y langostinos fritos con yucas",
                "precio_base": Decimal("38.00"),
                "id_categoria": self.categorias["Chicharrones"].id,
                "imagen_path": "https://drive.google.com/file/d/1eoiQJqdR3SHjeBqcufrNGNnzZJKwgaUf/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            # ARROCES
            {
                "nombre": "Arroz con Mariscos",
                "descripcion": "Arroz marinero con langostinos, conchas, calamar y pulpo en salsa especial",
                "precio_base": Decimal("35.00"),
                "id_categoria": self.categorias["Arroces"].id,
                "imagen_path": "https://drive.google.com/file/d/1f5J4b16DYg2YYQ3dR4sH5DJzF9HsT2pq/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Arroz Chaufa de Mariscos",
                "descripcion": "Arroz frito al wok con mariscos, cebolla china y sillao",
                "precio_base": Decimal("32.00"),
                "id_categoria": self.categorias["Arroces"].id,
                "imagen_path": "https://drive.google.com/file/d/13YU5MJXp2ai1-Utyo5v9IpS5Dg2te0gw/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            {
                "nombre": "Tacu Tacu con Mariscos",
                "descripcion": "Tacu tacu de frijoles con mariscos salteados y salsa criolla",
                "precio_base": Decimal("38.00"),
                "id_categoria": self.categorias["Arroces"].id,
                "imagen_path": "https://drive.google.com/file/d/1UUncdgoiAw-af4HLBKz7_S0AiJAqDaV_/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            # CAUSAS
            {
                "nombre": "Causa Rellena de Langostinos",
                "descripcion": "Causa de papa amarilla rellena de langostinos en mayonesa, aguacate y huevo",
                "precio_base": Decimal("28.00"),
                "id_categoria": self.categorias["Causas"].id,
                "imagen_path": "https://drive.google.com/file/d/1Q6PhiC41IaNk4-rzTf5hPJOS_UcXlxSi/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Causa de Pulpo",
                "descripcion": "Causa rellena de pulpo al olivo con aceitunas y palta",
                "precio_base": Decimal("30.00"),
                "id_categoria": self.categorias["Causas"].id,
                "imagen_path": "https://drive.google.com/file/d/1qdxy8MH-XXac8cWwRWeMm2_GHsESYp_g/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            {
                "nombre": "Causa Especial",
                "descripcion": "Triple causa: langostinos, atún y palta con salsa golf",
                "precio_base": Decimal("35.00"),
                "id_categoria": self.categorias["Causas"].id,
                "imagen_path": "https://drive.google.com/file/d/1busoPwLfMp0FgxAo9g1pc0kcPZazw1ln/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            # BEBIDAS
            {
                "nombre": "Chicha Morada",
                "descripcion": "Chicha morada natural preparada con maíz morado, piña y especias",
                "precio_base": Decimal("8.00"),
                "id_categoria": self.categorias["Bebidas"].id,
                "imagen_path": "https://drive.google.com/file/d/1_w-Wk393ouoSeZdlkSLrWGbNMA7N61xj/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Limonada Frozen",
                "descripcion": "Limonada frozen con hielo y hierba buena",
                "precio_base": Decimal("10.00"),
                "id_categoria": self.categorias["Bebidas"].id,
                "imagen_path": "https://drive.google.com/file/d/1fbXhbre-TzuqinCYw5637T375-a8f1Go/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Pisco Sour",
                "descripcion": "Clásico pisco sour con pisco quebranta, limón, jarabe y clara de huevo",
                "precio_base": Decimal("18.00"),
                "id_categoria": self.categorias["Bebidas"].id,
                "imagen_path": "https://drive.google.com/file/d/1V5NGG5U4HCbPTEOZkC3UC8OZQlQLSrlQ/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Chilcano de Pisco",
                "descripcion": "Pisco, ginger ale, limón y hielo",
                "precio_base": Decimal("15.00"),
                "id_categoria": self.categorias["Bebidas"].id,
                "imagen_path": "https://drive.google.com/file/d/1QlMnH9bRnnJGrZT6MU8Yj2ddOkl9knKK/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            {
                "nombre": "Inca Kola 1.5L",
                "descripcion": "Gaseosa Inca Kola botella de 1.5 litros",
                "precio_base": Decimal("7.00"),
                "id_categoria": self.categorias["Bebidas"].id,
                "imagen_path": "https://drive.google.com/file/d/14KIxsU03UQhq80ijLqdEDJXB0HLgLqr7/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            {
                "nombre": "Agua Mineral San Luis",
                "descripcion": "Agua mineral sin gas 625ml",
                "precio_base": Decimal("4.00"),
                "id_categoria": self.categorias["Bebidas"].id,
                "imagen_path": "https://drive.google.com/file/d/1yJ9gMthGnBnaV6kXLM7pENmiFT5K5u3Z/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            # POSTRES
            {
                "nombre": "Suspiro Limeño",
                "descripcion": "Manjar blanco con merengue italiano y oporto",
                "precio_base": Decimal("12.00"),
                "id_categoria": self.categorias["Postres"].id,
                "imagen_path": "https://drive.google.com/file/d/156YIcyAetJUtoqk-8b07LWETKNdjp4IO/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Mazamorra Morada",
                "descripcion": "Mazamorra de maíz morado con frutas y arroz con leche",
                "precio_base": Decimal("10.00"),
                "id_categoria": self.categorias["Postres"].id,
                "imagen_path": "https://drive.google.com/file/d/1rXynhqY70wt9UNn0haszs2y0s_5Me6ZF/view?usp=sharing",
                "disponible": True,
                "destacado": False
            },
            {
                "nombre": "Picarones",
                "descripcion": "Picarones de zapallo y camote con miel de chancaca",
                "precio_base": Decimal("12.00"),
                "id_categoria": self.categorias["Postres"].id,
                "imagen_path": "https://drive.google.com/file/d/1SnEdVTnPECzLKSRwnEHuErbMPDAHFi5h/view?usp=sharing",
                "disponible": True,
                "destacado": True
            },
            {
                "nombre": "Crema Volteada",
                "descripcion": "Flan de huevo con caramelo",
                "precio_base": Decimal("10.00"),
                "id_categoria": self.categorias["Postres"].id,
                "imagen_path": "https://drive.google.com/file/d/1WxJ46tSOhXDVaVi92_4NRx5lk5NHc80e/view?usp=sharing",
                "disponible": True,
                "destacado": False
            }
        ]
        
        for data in productos_data:
            producto = ProductoModel(**data)
            self.session.add(producto)
            self.productos[data["nombre"]] = producto
            print(f"   ✓ {data['nombre']}")
        
        await self.session.commit()
        print(f"   → {len(productos_data)} productos creados\n")
    
    async def seed_productos_alergenos(self):
        """Relaciona productos con sus alérgenos."""
        print("🔗 Creando relaciones producto-alérgeno...")
        
        # Refrescar productos y alérgenos para tener IDs
        for producto in self.productos.values():
            await self.session.refresh(producto)
        for alergeno in self.alergenos.values():
            await self.session.refresh(alergeno)
        
        # Definir relaciones producto-alérgeno
        relaciones = [
            ("Ceviche Clásico", "Pescado", NivelPresencia.CONTIENE, "Preparado con pescado fresco del día"),
            ("Ceviche Clásico", "Ají", NivelPresencia.CONTIENE, "Contiene ají limo"),
            ("Ceviche Mixto", "Pescado", NivelPresencia.CONTIENE, None),
            ("Ceviche Mixto", "Mariscos", NivelPresencia.CONTIENE, "Langostinos incluidos"),
            ("Ceviche Mixto", "Moluscos", NivelPresencia.CONTIENE, "Pulpo y calamar"),
            ("Ceviche Mixto", "Ají", NivelPresencia.CONTIENE, "Rocoto molido"),
            ("Ceviche de Conchas Negras", "Moluscos", NivelPresencia.CONTIENE, "Conchas negras frescas"),
            ("Ceviche de Conchas Negras", "Ají", NivelPresencia.CONTIENE, None),
            ("Ceviche de Pulpo", "Moluscos", NivelPresencia.CONTIENE, "Pulpo tierno"),
            ("Ceviche de Pulpo", "Ají", NivelPresencia.CONTIENE, "Ají amarillo"),
            ("Tiradito Clásico", "Pescado", NivelPresencia.CONTIENE, None),
            ("Tiradito Clásico", "Ají", NivelPresencia.CONTIENE, "Ají amarillo y rocoto"),
            ("Tiradito Nikkei", "Pescado", NivelPresencia.CONTIENE, None),
            ("Tiradito Nikkei", "Soja", NivelPresencia.CONTIENE, "Salsa sillao"),
            ("Tiradito Nikkei", "Ají", NivelPresencia.CONTIENE, None),
            ("Tiradito de Atún", "Pescado", NivelPresencia.CONTIENE, "Atún fresco"),
            ("Tiradito de Atún", "Ají", NivelPresencia.CONTIENE, "Ají limo"),
            ("Chicharrón de Pescado", "Pescado", NivelPresencia.CONTIENE, None),
            ("Chicharrón de Pescado", "Gluten", NivelPresencia.CONTIENE, "Empanizado"),
            ("Chicharrón de Calamar", "Moluscos", NivelPresencia.CONTIENE, "Calamar"),
            ("Chicharrón de Calamar", "Gluten", NivelPresencia.CONTIENE, "Empanizado"),
            ("Chicharrón de Calamar", "Lácteos", NivelPresencia.TRAZAS, "Salsa tártara"),
            ("Chicharrón Mixto", "Pescado", NivelPresencia.CONTIENE, None),
            ("Chicharrón Mixto", "Mariscos", NivelPresencia.CONTIENE, "Langostinos"),
            ("Chicharrón Mixto", "Moluscos", NivelPresencia.CONTIENE, "Calamar"),
            ("Chicharrón Mixto", "Gluten", NivelPresencia.CONTIENE, "Empanizado"),
            ("Arroz con Mariscos", "Mariscos", NivelPresencia.CONTIENE, "Variedad de mariscos"),
            ("Arroz con Mariscos", "Moluscos", NivelPresencia.CONTIENE, "Calamar y pulpo"),
            ("Arroz con Mariscos", "Ají", NivelPresencia.CONTIENE, None),
            ("Arroz Chaufa de Mariscos", "Mariscos", NivelPresencia.CONTIENE, None),
            ("Arroz Chaufa de Mariscos", "Soja", NivelPresencia.CONTIENE, "Salsa sillao"),
            ("Tacu Tacu con Mariscos", "Mariscos", NivelPresencia.CONTIENE, None),
            ("Tacu Tacu con Mariscos", "Ají", NivelPresencia.PUEDE_CONTENER, "Salsa criolla"),
            ("Causa Rellena de Langostinos", "Mariscos", NivelPresencia.CONTIENE, "Langostinos"),
            ("Causa Rellena de Langostinos", "Lácteos", NivelPresencia.TRAZAS, "Mayonesa"),
            ("Causa Rellena de Langostinos", "Ají", NivelPresencia.CONTIENE, "Ají amarillo en la masa"),
            ("Causa de Pulpo", "Moluscos", NivelPresencia.CONTIENE, "Pulpo"),
            ("Causa de Pulpo", "Ají", NivelPresencia.CONTIENE, "Ají amarillo"),
            ("Causa Especial", "Mariscos", NivelPresencia.CONTIENE, "Langostinos"),
            ("Causa Especial", "Pescado", NivelPresencia.CONTIENE, "Atún"),
            ("Causa Especial", "Lácteos", NivelPresencia.TRAZAS, "Salsa golf"),
            ("Causa Especial", "Ají", NivelPresencia.CONTIENE, None),
            ("Suspiro Limeño", "Lácteos", NivelPresencia.CONTIENE, "Manjar blanco"),
            ("Picarones", "Gluten", NivelPresencia.CONTIENE, "Harina de trigo"),
            ("Crema Volteada", "Lácteos", NivelPresencia.CONTIENE, "Leche evaporada"),
        ]
        
        count = 0
        for nombre_producto, nombre_alergeno, nivel, notas in relaciones:
            if nombre_producto in self.productos and nombre_alergeno in self.alergenos:
                relacion = ProductoAlergenoModel(
                    id_producto=self.productos[nombre_producto].id,
                    id_alergeno=self.alergenos[nombre_alergeno].id,
                    nivel_presencia=nivel,
                    notas=notas,
                    activo=True
                )
                self.session.add(relacion)
                count += 1
        
        await self.session.commit()
        print(f"   → {count} relaciones creadas\n")
    
    async def seed_tipos_opciones(self):
        """Crea tipos de opciones para productos."""
        print("⚙️  Creando tipos de opciones...")
        
        tipos_opciones_data = [
            {
                "codigo": "nivel_aji",
                "nombre": "Nivel de Ají",
                "descripcion": "Intensidad del picante en el plato",
                "activo": True,
                "orden": 1
            },
            {
                "codigo": "acompanamiento",
                "nombre": "Acompañamiento",
                "descripcion": "Extras que complementan el plato",
                "activo": True,
                "orden": 2
            },
            {
                "codigo": "temperatura",
                "nombre": "Temperatura",
                "descripcion": "Temperatura de la bebida",
                "activo": True,
                "orden": 3
            },
            {
                "codigo": "tamano",
                "nombre": "Tamaño",
                "descripcion": "Tamaño de la porción",
                "activo": True,
                "orden": 4
            }
        ]
        
        for data in tipos_opciones_data:
            tipo_opcion = TipoOpcionModel(**data)
            self.session.add(tipo_opcion)
            self.tipos_opciones[data["codigo"]] = tipo_opcion
            print(f"   ✓ {data['nombre']}")
        
        await self.session.commit()
        print(f"   → {len(tipos_opciones_data)} tipos de opciones creados\n")
    
    async def seed_productos_opciones(self):
        """Crea opciones específicas para cada producto."""
        print("🎛️  Creando opciones de productos...")
        
        # Refrescar productos y tipos de opciones para tener IDs
        for producto in self.productos.values():
            await self.session.refresh(producto)
        for tipo_opcion in self.tipos_opciones.values():
            await self.session.refresh(tipo_opcion)
        
        # Opciones de Nivel de Ají (aplica a ceviches, tiraditos, arroces)
        productos_con_aji = [
            "Ceviche Clásico", "Ceviche Mixto", "Ceviche de Conchas Negras", "Ceviche de Pulpo",
            "Tiradito Clásico", "Tiradito Nikkei", "Tiradito de Atún",
            "Arroz con Mariscos", "Arroz Chaufa de Mariscos", "Tacu Tacu con Mariscos"
        ]
        
        opciones_nivel_aji = [
            ("Sin ají", Decimal("0.00"), 1),
            ("Ají suave", Decimal("0.00"), 2),
            ("Ají normal", Decimal("0.00"), 3),
            ("Ají picante", Decimal("0.00"), 4),
            ("Ají extra picante", Decimal("2.00"), 5),  # Cobra extra por rocoto especial
        ]
        
        count = 0
        for nombre_producto in productos_con_aji:
            if nombre_producto in self.productos:
                for nombre, precio, orden in opciones_nivel_aji:
                    opcion = ProductoOpcionModel(
                        id_producto=self.productos[nombre_producto].id,
                        id_tipo_opcion=self.tipos_opciones["nivel_aji"].id,
                        nombre=nombre,
                        precio_adicional=precio,
                        activo=True,
                        orden=orden
                    )
                    self.session.add(opcion)
                    count += 1
        
        # Opciones de Acompañamiento (para ceviches y chicharrones)
        productos_con_acompanamiento = [
            "Ceviche Clásico", "Ceviche Mixto", "Ceviche de Conchas Negras", "Ceviche de Pulpo",
            "Chicharrón de Pescado", "Chicharrón de Calamar", "Chicharrón Mixto"
        ]
        
        opciones_acompanamiento = [
            ("Con camote", Decimal("3.00"), 1),
            ("Con choclo", Decimal("3.00"), 2),
            ("Con yuca", Decimal("3.50"), 3),
            ("Con cancha", Decimal("2.00"), 4),
            ("Mixto (camote + choclo)", Decimal("5.00"), 5),
        ]
        
        for nombre_producto in productos_con_acompanamiento:
            if nombre_producto in self.productos:
                for nombre, precio, orden in opciones_acompanamiento:
                    opcion = ProductoOpcionModel(
                        id_producto=self.productos[nombre_producto].id,
                        id_tipo_opcion=self.tipos_opciones["acompanamiento"].id,
                        nombre=nombre,
                        precio_adicional=precio,
                        activo=True,
                        orden=orden
                    )
                    self.session.add(opcion)
                    count += 1
        
        # Opciones de Temperatura (para bebidas)
        productos_bebidas = ["Chicha Morada", "Limonada Frozen", "Inca Kola"]
        
        opciones_temperatura = [
            ("Natural", Decimal("0.00"), 1),
            ("Helada", Decimal("1.00"), 2),
            ("Con hielo", Decimal("0.50"), 3),
        ]
        
        for nombre_producto in productos_bebidas:
            if nombre_producto in self.productos:
                for nombre, precio, orden in opciones_temperatura:
                    opcion = ProductoOpcionModel(
                        id_producto=self.productos[nombre_producto].id,
                        id_tipo_opcion=self.tipos_opciones["temperatura"].id,
                        nombre=nombre,
                        precio_adicional=precio,
                        activo=True,
                        orden=orden
                    )
                    self.session.add(opcion)
                    count += 1
        
        # Opciones de Tamaño (para algunos platos)
        productos_con_tamano = [
            "Ceviche Clásico", "Ceviche Mixto", "Arroz con Mariscos", 
            "Chicha Morada", "Limonada Frozen"
        ]
        
        opciones_tamano = [
            ("Personal", Decimal("0.00"), 1),
            ("Para 2 personas", Decimal("15.00"), 2),
            ("Familiar (4 personas)", Decimal("30.00"), 3),
        ]
        
        for nombre_producto in productos_con_tamano:
            if nombre_producto in self.productos:
                for nombre, precio, orden in opciones_tamano:
                    opcion = ProductoOpcionModel(
                        id_producto=self.productos[nombre_producto].id,
                        id_tipo_opcion=self.tipos_opciones["tamano"].id,
                        nombre=nombre,
                        precio_adicional=precio,
                        activo=True,
                        orden=orden
                    )
                    self.session.add(opcion)
                    self.productos_opciones[count] = opcion
                    count += 1
        
        await self.session.commit()
        print(f"   → {count} opciones de productos creadas\n")


async def main():
    """Función principal para ejecutar el seed."""
    
    database_url = get_database_url()
    print(f"📊 Conectando a base de datos: {database_url}\n")
    
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        seeder = CevicheriaSeeder(session)
        await seeder.seed_all()
    
    await engine.dispose()
    
    print(f"\n📍 Datos guardados en: {Path('instance/restaurant.db').absolute()}")


if __name__ == "__main__":
    print("="*60)
    print("   CEVICHERÍA EL MAR PERUANO - Seed Database")
    print("="*60)
    asyncio.run(main())