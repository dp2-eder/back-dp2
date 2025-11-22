"""
Script para enriquecer datos existentes de productos con:
- Alrgenos (crear 8)
- Tipos de opciones (crear 4)
- Relaciones producto-alrgeno (asociar inteligentemente)
- Opciones de productos (crear y asociar)


 NO crea productos ni categoras nuevas.
Solo agrega informacin complementaria a los 274 productos existentes.

Ejecutar con:
    python -m scripts.enrich_existing_data
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
import unicodedata

# Agregar el directorio raz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from src.models.auth.sesion_model import SesionModel
from src.models.menu.categoria_model import CategoriaModel
from src.models.menu.alergeno_model import AlergenoModel
from src.models.menu.producto_model import ProductoModel
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
# from src.models.auth.rol_model import RolModel  # ELIMINADO: Ya no se usa RolModel
from src.models.mesas.local_model import LocalModel
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.locales_categorias_model import LocalesCategoriasModel
from src.models.mesas.locales_productos_model import LocalesProductosModel
from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel
from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel
from src.core.enums.alergeno_enums import NivelPresencia
from src.core.enums.local_enums import TipoLocal
from src.core.enums.mesa_enums import EstadoMesa
from src.core.enums.sesion_enums import EstadoSesion

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


class DataEnricher:
    """Enriquecedor de datos existentes."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.productos_existentes = {}  # {nombre_normalizado: ProductoModel}
        self.categorias_existentes = {}  # {nombre_normalizado: CategoriaModel}
        self.alergenos = {}  # {nombre: AlergenoModel}
        self.tipos_opciones = {}  # {codigo: TipoOpcionModel}
        self.local = None  # LocalModel (creado en create_local)
    
    @staticmethod
    def normalize_name(nombre: str) -> str:
        """
        Normaliza nombres para matching (maysculas, sin tildes, sin espacios extra).
        
        Ejemplo:
            "Ceviche Limeo"  "CEVICHE LIMENO"
        """
        # Remover tildes
        nombre = ''.join(
            c for c in unicodedata.normalize('NFD', nombre)
            if unicodedata.category(c) != 'Mn'
        )
        # Maysculas y strip
        return nombre.upper().strip()

    async def create_local(self):
        """
        PASO 0.1: Crear el local 'Barra Arena' si no existe.
        """
        print("\n" + "="*70)
        print(" PASO 0.1: CREANDO LOCAL")
        print("="*70)

        # Buscar si ya existe
        result = await self.session.execute(
            select(LocalModel).where(LocalModel.codigo == "BA-001")
        )
        existing_local = result.scalars().first()

        if existing_local:
            print(f"   Local '{existing_local.nombre}' ya existe (ID: {existing_local.id})")
            self.local = existing_local
            return

        # Crear nuevo local
        self.local = LocalModel(
            codigo="BA-001",
            nombre="Barra Arena",
            direccion="CAL. GENERAL BORGONO N 199",
            distrito="MIRAFLORES",
            ciudad="LIMA",
            telefono=None,
            email=None,
            tipo_local=TipoLocal.CENTRAL,
            capacidad_total=None,
            activo=True,
            fecha_apertura=None
        )

        self.session.add(self.local)
        await self.session.flush()
        await self.session.refresh(self.local)

        print(f"   Local creado: '{self.local.nombre}' (ID: {self.local.id})")
        sesion = SesionModel(id_domotica="DOM-001", id_local=self.local.id, estado=EstadoSesion.ACTIVO, orden=1)
        self.session.add_all([sesion])
        await self.session.commit()
        print(f"Locales y sesiones de prueba creadas exitosamente.")


    async def load_existing_data(self):
        """
         SOLO consulta productos y categoras existentes para hacer matching.
        NO crea nada nuevo.
        """
        print("\n" + "="*70)
        print(" CARGANDO DATOS EXISTENTES DE LA BASE DE DATOS")
        print("="*70)
        
        # Contar productos
        result = await self.session.execute(select(func.count(ProductoModel.id)))
        count_productos = result.scalar()
        print(f" Productos encontrados: {count_productos}")
        
        # Contar categoras
        result = await self.session.execute(select(func.count(CategoriaModel.id)))
        count_categorias = result.scalar()
        print(f" Categoras encontradas: {count_categorias}")
        
        if count_productos == 0:
            print("\n ERROR: No hay productos en la BD.")
            print("   Ejecuta primero el scrapper para cargar productos.")
            raise RuntimeError(
                "No hay productos en la base de datos. "
                "Ejecuta primero el endpoint /api/v1/sync/platos para sincronizar productos."
            )
        
        # Cargar TODOS los productos (274)
        result = await self.session.execute(select(ProductoModel))
        productos = result.scalars().all()
        
        for producto in productos:
            nombre_key = self.normalize_name(producto.nombre)
            self.productos_existentes[nombre_key] = producto
        
        print(f"    {len(self.productos_existentes)} productos mapeados por nombre")
        
        # Cargar categoras (23)
        result = await self.session.execute(select(CategoriaModel))
        categorias = result.scalars().all()
        
        for categoria in categorias:
            nombre_key = self.normalize_name(categoria.nombre)
            self.categorias_existentes[nombre_key] = categoria
        
        print(f"    {len(self.categorias_existentes)} categoras mapeadas por nombre")
        print("="*70 + "\n")
    
    async def create_alergenos(self):
        """
          PASO 2: Crear los 8 alrgenos comunes en cevicheras.
        """
        print("\n" + "="*70)
        print("  CREANDO ALRGENOS")
        print("="*70)
        
        # Verificar si ya existen alrgenos
        result = await self.session.execute(select(func.count(AlergenoModel.id)))
        count_alergenos = result.scalar()
        
        if count_alergenos and count_alergenos > 0:
            print(f"     Ya existen {count_alergenos} alrgenos en la BD.")
            print("   Cargando alrgenos existentes...")
            
            # Cargar alrgenos existentes
            result = await self.session.execute(select(AlergenoModel))
            alergenos_existentes = result.scalars().all()
            
            for alergeno in alergenos_existentes:
                self.alergenos[alergeno.nombre] = alergeno
                print(f"    {alergeno.nombre:<20} (ya exista)")
            
            print("="*70 + "\n")
            return
        
        alergenos_data = [
            {
                "nombre": "Mariscos",
                "descripcion": "Langostinos, camarones, pulpo, calamar, conchas negras",
                "activo": True
            },
            {
                "nombre": "Pescado",
                "descripcion": "Lenguado, corvina, mero, bonito, atn",
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
                "nombre": "Lcteos",
                "descripcion": "Leche, queso, crema de leche",
                "activo": True
            },
            {
                "nombre": "Aj",
                "descripcion": "Rocoto, aj amarillo, aj limo",
                "activo": True
            },
            {
                "nombre": "Soja",
                "descripcion": "Salsa de soja y derivados",
                "activo": True
            },
            {
                "nombre": "Frutos Secos",
                "descripcion": "Man, nueces, almendras",
                "activo": True
            }
        ]
        
        for data in alergenos_data:
            alergeno = AlergenoModel(**data)
            self.session.add(alergeno)
            self.alergenos[data["nombre"]] = alergeno
            print(f"    {data['nombre']:<20} - {data['descripcion']}")
        
        await self.session.commit()
        
        # Refrescar para obtener IDs
        for alergeno in self.alergenos.values():
            await self.session.refresh(alergeno)
        
        print(f"\n    {len(alergenos_data)} alrgenos creados exitosamente")
        print("="*70 + "\n")
    
    async def create_tipos_opciones(self):
        """
          PASO 3: Crear 4 tipos de opciones (con seleccion_minima/maxima).
        """
        print("\n" + "="*70)
        print("  CREANDO TIPOS DE OPCIONES")
        print("="*70)
        
        # Verificar si ya existen tipos de opciones
        result = await self.session.execute(select(func.count(TipoOpcionModel.id)))
        count_tipos = result.scalar()
        
        if count_tipos and count_tipos > 0:
            print(f"     Ya existen {count_tipos} tipos de opciones en la BD.")
            print("   Cargando tipos existentes...")
            
            # Cargar tipos existentes
            result = await self.session.execute(select(TipoOpcionModel))
            tipos_existentes = result.scalars().all()
            
            for tipo in tipos_existentes:
                self.tipos_opciones[tipo.codigo] = tipo
                max_str = str(tipo.seleccion_maxima) if tipo.seleccion_maxima is not None else ""
                print(f"    {tipo.nombre:<20} (ya exista, min:{tipo.seleccion_minima}, max:{max_str})")
            
            print("="*70 + "\n")
            return
        
        tipos_data = [
            {
                "codigo": "nivel_aji",
                "nombre": "Nivel de Aj",
                "descripcion": "Intensidad del picante en el plato",
                "seleccion_minima": 0,  # Opcional
                "seleccion_maxima": 1,  # Mximo 1
                "activo": True,
                "orden": 1
            },
            {
                "codigo": "acompanamiento",
                "nombre": "Acompaamiento",
                "descripcion": "Extras que complementan tu plato",
                "seleccion_minima": 0,  # Opcional
                "seleccion_maxima": None,  # Sin lmite (ilimitado)
                "activo": True,
                "orden": 2
            },
            {
                "codigo": "temperatura",
                "nombre": "Temperatura",
                "descripcion": "Temperatura de la bebida",
                "seleccion_minima": 0,  # Opcional
                "seleccion_maxima": 1,  # Exactamente 1
                "activo": True,
                "orden": 3
            },
            {
                "codigo": "tamano",
                "nombre": "Tamao",
                "descripcion": "Tamao de la porcin",
                "seleccion_minima": 1,  # Obligatorio
                "seleccion_maxima": 1,  # Exactamente 1
                "activo": True,
                "orden": 4
            }
        ]
        
        for data in tipos_data:
            tipo = TipoOpcionModel(**data)
            self.session.add(tipo)
            self.tipos_opciones[data["codigo"]] = tipo
            
            max_str = str(data["seleccion_maxima"]) if data["seleccion_maxima"] is not None else ""
            print(f"    {data['nombre']:<20} (min:{data['seleccion_minima']}, max:{max_str})")
        
        await self.session.commit()
        
        # Refrescar para obtener IDs
        for tipo in self.tipos_opciones.values():
            await self.session.refresh(tipo)
        
        print(f"\n    {len(tipos_data)} tipos de opciones creados exitosamente")
        print("="*70 + "\n")
    
    async def associate_alergenos_to_productos(self):
        """
         PASO 4: Asociar alrgenos a productos usando reglas inteligentes.
        """
        print("\n" + "="*70)
        print(" ASOCIANDO ALRGENOS A PRODUCTOS (Reglas inteligentes)")
        print("="*70)
        
        count = 0
        
        # ==================== REGLA 1: CEVICHES ====================
        print("\n Regla 1: CEVICHES  Pescado + Aj")
        for nombre_key, producto in self.productos_existentes.items():
            if 'CEVICHE' in nombre_key:
                # Todos los ceviches tienen Pescado + Aj
                await self._add_alergeno_relation(producto, "Pescado", NivelPresencia.CONTIENE)
                await self._add_alergeno_relation(producto, "Aj", NivelPresencia.CONTIENE)
                count += 2

                # Si es MIXTO  agregar Mariscos + Moluscos
                if 'MIXTO' in nombre_key:
                    await self._add_alergeno_relation(producto, "Mariscos", NivelPresencia.CONTIENE)
                    await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.CONTIENE)
                    count += 2

                # Si tiene CONCHAS  agregar Moluscos
                if 'CONCHAS' in nombre_key:
                    await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.CONTIENE)
                    count += 1
        
        print(f"    Procesados {sum(1 for k in self.productos_existentes if 'CEVICHE' in k)} ceviches")
        
        # ==================== REGLA 2: TIRADITOS ====================
        print("\n Regla 2: TIRADITOS  Pescado + Aj")
        for nombre_key, producto in self.productos_existentes.items():
            if 'TIRADITO' in nombre_key:
                await self._add_alergeno_relation(producto, "Pescado", NivelPresencia.CONTIENE)
                await self._add_alergeno_relation(producto, "Aj", NivelPresencia.CONTIENE)
                count += 2
                
                # Si es NIKKEI  Soja (sillao)
                if 'NIKKEI' in nombre_key:
                    await self._add_alergeno_relation(producto, "Soja", NivelPresencia.CONTIENE, "Salsa sillao")
                    count += 1
        
        print(f"    Procesados {sum(1 for k in self.productos_existentes if 'TIRADITO' in k)} tiraditos")
        
        # ==================== REGLA 3: CHICHARRONES ====================
        print("\n Regla 3: CHICHARRONES  Gluten (empanizado)")
        for nombre_key, producto in self.productos_existentes.items():
            if 'CHICHARRON' in nombre_key:
                await self._add_alergeno_relation(producto, "Gluten", NivelPresencia.CONTIENE, "Empanizado")
                count += 1
                
                if 'PESCADO' in nombre_key:
                    await self._add_alergeno_relation(producto, "Pescado", NivelPresencia.CONTIENE)
                    count += 1
                elif 'MIXTO' in nombre_key:
                    await self._add_alergeno_relation(producto, "Pescado", NivelPresencia.CONTIENE)
                    await self._add_alergeno_relation(producto, "Mariscos", NivelPresencia.CONTIENE)
                    await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.CONTIENE)
                    count += 3
                elif 'CALAMAR' in nombre_key or 'POTA' in nombre_key:
                    await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.CONTIENE)
                    count += 1
        
        print(f"    Procesados {sum(1 for k in self.productos_existentes if 'CHICHARRON' in k)} chicharrones")
        
        # ==================== REGLA 4: ARROCES CON MARISCOS ====================
        print("\n Regla 4: ARROCES CON MARISCOS")
        for nombre_key, producto in self.productos_existentes.items():
            if 'ARROZ' in nombre_key and any(word in nombre_key for word in ['MARISCOS', 'CONCHAS', 'LANGOSTINOS']):
                await self._add_alergeno_relation(producto, "Mariscos", NivelPresencia.CONTIENE)
                await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.PUEDE_CONTENER)
                await self._add_alergeno_relation(producto, "Aj", NivelPresencia.CONTIENE)
                count += 3
                
                if 'CHAUFA' in nombre_key:
                    await self._add_alergeno_relation(producto, "Soja", NivelPresencia.CONTIENE, "Salsa sillao")
                    count += 1
        
        print(f"    Procesados arroces con mariscos")
        
        # ==================== REGLA 5: CAUSAS ====================
        print("\n Regla 5: CAUSAS  Aj + Lcteos")
        for nombre_key, producto in self.productos_existentes.items():
            if 'CAUSA' in nombre_key:
                await self._add_alergeno_relation(producto, "Aj", NivelPresencia.CONTIENE, "Aj amarillo en masa")
                await self._add_alergeno_relation(producto, "Lcteos", NivelPresencia.TRAZAS, "Mayonesa")
                count += 2
                
                if 'LANGOSTINOS' in nombre_key or 'CANGREJO' in nombre_key:
                    await self._add_alergeno_relation(producto, "Mariscos", NivelPresencia.CONTIENE)
                    count += 1
                elif 'PULPO' in nombre_key:
                    await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.CONTIENE)
                    count += 1
        
        print(f"    Procesadas {sum(1 for k in self.productos_existentes if 'CAUSA' in k)} causas")
        
        # ==================== REGLA 6: SOPAS ====================
        print("\n Regla 6: SOPAS (Parihuela, Chupe, Sudado, etc.)")
        for nombre_key, producto in self.productos_existentes.items():
            if any(sopa in nombre_key for sopa in ['PARIHUELA', 'CHUPE', 'SUDADO', 'AGUADITO', 'CHILCANITO']):
                if 'MARISCOS' in nombre_key or 'MIXTA' in nombre_key:
                    await self._add_alergeno_relation(producto, "Mariscos", NivelPresencia.CONTIENE)
                    await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.PUEDE_CONTENER)
                    count += 2
                elif 'PESCADO' in nombre_key:
                    await self._add_alergeno_relation(producto, "Pescado", NivelPresencia.CONTIENE)
                    count += 1
        
        print(f"    Procesadas sopas")
        
        # ==================== REGLA 7: LOMO SALTADO ====================
        print("\n Regla 7: LOMO SALTADO  Soja (posible)")
        for nombre_key, producto in self.productos_existentes.items():
            if 'LOMO' in nombre_key and 'SALTADO' in nombre_key:
                await self._add_alergeno_relation(producto, "Soja", NivelPresencia.PUEDE_CONTENER, "Salsa sillao")
                count += 1
        
        print(f"    Procesados lomos saltados")
        
        # ==================== REGLA 8: CONCHAS A LA PARMESANA ====================
        print("\n Regla 8: CONCHAS A LA PARMESANA  Moluscos + Lcteos")
        for nombre_key, producto in self.productos_existentes.items():
            if 'PARMESANA' in nombre_key:
                await self._add_alergeno_relation(producto, "Moluscos", NivelPresencia.CONTIENE, "Conchas")
                await self._add_alergeno_relation(producto, "Lcteos", NivelPresencia.CONTIENE, "Queso parmesano")
                count += 2
        
        print(f"    Procesadas conchas a la parmesana")
        
        # ==================== REGLA 9: LECHE DE TIGRE ====================
        print("\n Regla 9: LECHE DE TIGRE  Pescado + Aj")
        for nombre_key, producto in self.productos_existentes.items():
            if 'LECHE DE TIGRE' in nombre_key or 'LECHE TIGRE' in nombre_key:
                await self._add_alergeno_relation(producto, "Pescado", NivelPresencia.CONTIENE)
                await self._add_alergeno_relation(producto, "Aj", NivelPresencia.CONTIENE)
                count += 2
        
        print(f"    Procesadas leches de tigre")
        
        await self.session.commit()
        
        print(f"\n{'='*70}")
        print(f"    TOTAL: {count} relaciones producto-alrgeno creadas")
        print(f"{'='*70}\n")
    
    async def _add_alergeno_relation(
        self,
        producto: ProductoModel,
        alergeno_nombre: str,
        nivel: NivelPresencia,
        notas: str | None = None
    ):
        """
        Helper para agregar relacin producto-alrgeno (con verificacin de duplicados).

        Args:
            producto: Modelo del producto
            alergeno_nombre: Nombre del alrgeno (debe existir en self.alergenos)
            nivel: Nivel de presencia (CONTIENE, PUEDE_CONTENER, TRAZAS)
            notas: Notas adicionales (opcional)
        """
        if alergeno_nombre in self.alergenos:
            # Verificar si ya existe esta relacin
            result = await self.session.execute(
                select(ProductoAlergenoModel).where(
                    ProductoAlergenoModel.id_producto == producto.id,
                    ProductoAlergenoModel.id_alergeno == self.alergenos[alergeno_nombre].id
                )
            )
            existing = result.scalars().first()

            if not existing:
                # Solo crear si no existe
                relacion = ProductoAlergenoModel(
                    id_producto=producto.id,
                    id_alergeno=self.alergenos[alergeno_nombre].id,
                    nivel_presencia=nivel,
                    notas=notas,
                    activo=True
                )
                self.session.add(relacion)
    
    async def create_opciones_for_productos(self):
        """
          PASO 5: Crear opciones especficas para productos reales.
        """
        print("\n" + "="*70)
        print("  CREANDO OPCIONES DE PRODUCTOS")
        print("="*70)
        
        count = 0
        
        # ==================== OPCIONES DE NIVEL DE AJ ====================
        print("\n  Opciones de Nivel de Aj (para ceviches, tiraditos, arroces)")
        opciones_aji = [
            ("Sin aj", Decimal("0.00"), 1),
            ("Aj suave", Decimal("0.00"), 2),
            ("Aj normal", Decimal("0.00"), 3),
            ("Aj picante", Decimal("1.00"), 4),
            ("Aj extra picante", Decimal("2.00"), 5),
        ]
        
        productos_con_aji = 0
        for nombre_key, producto in self.productos_existentes.items():
            if any(word in nombre_key for word in ['CEVICHE', 'TIRADITO', 'ARROZ', 'LECHE DE TIGRE', 'LECHE TIGRE']):
                for nombre, precio, orden in opciones_aji:
                    self._add_opcion(producto, "nivel_aji", nombre, precio, orden)
                    count += 1
                productos_con_aji += 1
        
        print(f"    {productos_con_aji} productos con opciones de aj ({productos_con_aji * 5} opciones)")
        
        # ==================== OPCIONES DE ACOMPAAMIENTO ====================
        print("\n Opciones de Acompaamiento (ceviches, chicharrones)")
        opciones_acomp = [
            ("Con camote", Decimal("3.00"), 1),
            ("Con choclo", Decimal("3.00"), 2),
            ("Con yuca", Decimal("3.50"), 3),
            ("Con cancha", Decimal("2.00"), 4),
        ]
        
        productos_con_acomp = 0
        for nombre_key, producto in self.productos_existentes.items():
            if any(word in nombre_key for word in ['CEVICHE', 'CHICHARRON', 'TIRADITO']):
                for nombre, precio, orden in opciones_acomp:
                    self._add_opcion(producto, "acompanamiento", nombre, precio, orden)
                    count += 1
                productos_con_acomp += 1
        
        print(f"    {productos_con_acomp} productos con acompaamientos ({productos_con_acomp * 4} opciones)")
        
        # ==================== OPCIONES DE TEMPERATURA ====================
        print("\n Opciones de Temperatura (bebidas)")
        opciones_temp = [
            ("Natural", Decimal("0.00"), 1),
            ("Helada", Decimal("1.00"), 2),
            ("Con hielo", Decimal("0.50"), 3),
        ]
        
        productos_con_temp = 0
        for nombre_key, producto in self.productos_existentes.items():
            # Detectar bebidas (contienen ML, CHICHA, nombres de cervezas, etc.)
            if any(word in nombre_key for word in ['ML', 'CHICHA', 'LIMONADA', 'PILSEN', 'INCA', 'CORONA', 'HEINEKEN', 'CRISTAL', 'CUSQUEA']):
                for nombre, precio, orden in opciones_temp:
                    self._add_opcion(producto, "temperatura", nombre, precio, orden)
                    count += 1
                productos_con_temp += 1
        
        print(f"    {productos_con_temp} bebidas con opciones de temperatura ({productos_con_temp * 3} opciones)")
        
        # ==================== OPCIONES DE TAMAO ====================
        print("\n Opciones de Tamao (platos principales)")
        opciones_tamano = [
            ("Personal", Decimal("0.00"), 1),
            ("Para 2 personas", Decimal("15.00"), 2),
            ("Familiar (4 personas)", Decimal("30.00"), 3),
        ]
        
        productos_con_tamano = 0
        for nombre_key, producto in self.productos_existentes.items():
            if any(word in nombre_key for word in ['CEVICHE', 'ARROZ', 'CHICHARRON', 'PARIHUELA', 'CHUPE', 'SUDADO']):
                # Solo si NO dice "FUENTE" (las fuentes ya son grandes)
                if 'FUENTE' not in nombre_key:
                    for nombre, precio, orden in opciones_tamano:
                        self._add_opcion(producto, "tamano", nombre, precio, orden)
                        count += 1
                    productos_con_tamano += 1
        
        print(f"    {productos_con_tamano} platos con opciones de tamao ({productos_con_tamano * 3} opciones)")
        
        await self.session.commit()
        
        print(f"\n{'='*70}")
        print(f"    TOTAL: {count} opciones de productos creadas")
        print(f"{'='*70}\n")
    
    def _add_opcion(
        self, 
        producto: ProductoModel, 
        tipo_codigo: str, 
        nombre: str, 
        precio: Decimal, 
        orden: int
    ):
        """
        Helper para agregar opcin a producto.
        
        Args:
            producto: Modelo del producto
            tipo_codigo: Cdigo del tipo de opcin (debe existir en self.tipos_opciones)
            nombre: Nombre de la opcin
            precio: Precio adicional
            orden: Orden de visualizacin
        """
        if tipo_codigo in self.tipos_opciones:
            opcion = ProductoOpcionModel(
                id_producto=producto.id,
                id_tipo_opcion=self.tipos_opciones[tipo_codigo].id,
                nombre=nombre,
                precio_adicional=precio,
                activo=True,
                orden=orden
            )
            self.session.add(opcion)
    
    # MÉTODO ELIMINADO: create_roles_if_not_exist()
    # Ya no se crean roles porque RolModel fue eliminado del sistema.
    # El nuevo sistema de login simplificado no usa roles.
    
    async def update_images_from_seed(self):
        """
          PASO 7: Actualizar imagen_path de productos/categoras reales
        usando las imgenes del seed cuando coincidan los nombres.
        """
        print("\n" + "="*70)
        print("  ACTUALIZANDO IMGENES DESDE SEED")
        print("="*70)
        
        # ==================== MAPEO DE IMGENES DE PRODUCTOS ====================
        productos_seed_imagenes = {
            # CEVICHES (ya tienen imagen los siguientes)
            "CEVICHE CLASICO": "https://drive.google.com/file/d/14MotvG3-NJLZO5bUJjGqyMkOMMSzOZ7L/view?usp=sharing",
            "CEVICHE MIXTO": "https://drive.google.com/file/d/18wtI2hmnm2mDhV73cU-ow6XJUUgzXVnP/view?usp=sharing",
            "CEVICHE DE CONCHAS NEGRAS": "https://drive.google.com/file/d/1qsrha511qKobIjyCV91PDmJxPcOz8tOd/view?usp=sharing",
            "CEVICHE DE PULPO": "https://drive.google.com/file/d/1dIm4pjLo3E2g_Zop6rvNXc8OErAmHuBd/view?usp=sharing",
            
            # CEVICHES (faltan imgenes - agregar URLs despus)
            "CEVICHE DE POTA": "",
            "CEVICHE NORTENO": "",
            "CEVICHE LIMENO": "https://drive.google.com/file/d/1ZaYA_c1ZGfl6tsPe80-fwSzpHR_LYzSZ/view?usp=sharing",
            "CEVICHE CARRETILLERO": "",
            "CEVICHE MIXTO NORTENO": "",
            "CEVICHE MIXTO LIMENO": "https://drive.google.com/file/d/1ZaYA_c1ZGfl6tsPe80-fwSzpHR_LYzSZ/view?usp=sharing",
            "CEVICHE DE CONCHAS NEGRAS CON LANGOSTINOS": "",
            "CEVICHE DE CONCHAS NEGRAS CON PULPO": "",
            "CEVICHE DE CONCHAS NEGRAS CON PESCADO": "",
            "CEVICHE PESCADO CON PULPO": "",
            "CONCHAS NEGRAS CON LANGOSTINOS Y PULPO": "",
            "FUENTE CEVICHE PESCADO": "https://drive.google.com/file/d/1ZaYA_c1ZGfl6tsPe80-fwSzpHR_LYzSZ/view?usp=sharing",
            "FUENTE CEVICHE DE POTA": "",
            "FUENTE CEVICHE MIXTO": "",
            "FUENTE BARRA ARENA": "",
            "FUENTE DE CEVICHE DE CORVINA": "",
            "TRILOGIA DE CEVICHES": "",
            
            # TIRADITOS (ya tienen imagen los siguientes)
            "TIRADITO CLASICO": "https://drive.google.com/file/d/1gXlCGBSnduNLxla2WA1kDnMnci7WpJHh/view?usp=sharing",
            "TIRADITO NIKKEI": "https://drive.google.com/file/d/1QNR6LydeY06cg_71gw376Iep3dZddvsI/view?usp=sharing",
            "TIRADITO DE ATUN": "https://drive.google.com/file/d/1Nv1fxVvE4zoEzdnQ44hoAhfQnRKiI2ov/view?usp=sharing",
            
            # TIRADITOS (faltan imgenes)
            "TIRADITO AJI AMARILLO": "",
            "TIRADITO BICOLOR": "",
            "TIRADITO CARRETILLERO": "",
            "TIRADITO BARRA ARENA": "",
            
            # CHICHARRONES (ya tienen imagen los siguientes)
            "CHICHARRON DE PESCADO": "https://drive.google.com/file/d/1-7MmcqQ0cWRFJUj2uuiXhGHHzGOZseDn/view?usp=sharing",
            "CHICHARRON DE CALAMAR": "https://drive.google.com/file/d/1i0KzBtnznRC71VMMT5ZUPnIbPky7vJYo/view?usp=sharing",
            "CHICHARRON MIXTO": "https://drive.google.com/file/d/1eoiQJqdR3SHjeBqcufrNGNnzZJKwgaUf/view?usp=sharing",
            
            # CHICHARRONES (faltan imgenes)
            "CHICHARRON DE PULPO": "https://drive.google.com/file/d/1qdabG7kbNr86IpRQALOw1mgQDxBRTnsC/view?usp=sharing",
            
            # ARROCES (ya tienen imagen los siguientes)
            "ARROZ CON MARISCOS": "https://drive.google.com/file/d/1f5J4b16DYg2YYQ3dR4sH5DJzF9HsT2pq/view?usp=sharing",
            "ARROZ CHAUFA DE MARISCOS": "https://drive.google.com/file/d/1UUncdgoiAw-af4HLBKz7_S0AiJAqDaV_/view?usp=sharing",
            "TACU TACU CON MARISCOS": "https://drive.google.com/file/d/12zU5d9MgOFY1tRjurnOMZ-QR38I-RHo2/view?usp=sharing",
            
            # ARROCES (faltan imgenes)
            "FILETE DE PESCADO A LA PLANCHA": "https://drive.google.com/file/d/1yRLGVNmJ5bYmf-v995gE3v5mf-1fjsqd/view?usp=sharing",
            "FILETE DE PESCADO FRITO": "https://drive.google.com/file/d/1yRLGVNmJ5bYmf-v995gE3v5mf-1fjsqd/view?usp=sharing",
            "CHAUFA DE PESCADO": "",
            "CHAUFA DE MARISCOS": "",
            "ARROZ NORTENO DE PESCADO": "",
            "ARROZ NORTENO DE MARISCOS": "",
            "FILETE A LO MACHO": "",
            "ARROZ CON CONCHAS NEGRAS": "",
            "ARROZ CON LANGOSTINOS": "",
            "CHAUFA DE LANGOSTINOS": "",
            "ARROZ CON HUEVO Y FREJOLES": "",
            "FUENTE DE CHAUFA DE MARISCOS": "",
            "FUENTE ARROZ CON MARISCOS": "",
            
            # CAUSAS (ya tienen imagen los siguientes)
            "CAUSA RELLENA DE LANGOSTINOS": "https://drive.google.com/file/d/1Q6PhiC41IaNk4-rzTf5hPJOS_UcXlxSi/view?usp=sharing",
            "CAUSA DE PULPO": "https://drive.google.com/file/d/1qdxy8MH-XXac8cWwRWeMm2_GHsESYp_g/view?usp=sharing",
            "CAUSA ESPECIAL": "https://drive.google.com/file/d/1busoPwLfMp0FgxAo9g1pc0kcPZazw1ln/view?usp=sharing",
            
            # CAUSAS (faltan imgenes)
            "CAUSA DE CANGREJO": "https://drive.google.com/file/d/1W4hdy1zz8WQ5-u3DXJlnw7p9on3Cbd5Q/view?usp=sharing",
            "CAUSA DE PULPO AL OLIVO": "https://drive.google.com/file/d/1rGDz0fOqxT9yhkouWdDthsInxauU4hu2/view?usp=sharing",
            "CAUSA ACEVICHADA LIMENA": "https://drive.google.com/file/d/1Sdvoadea5xZDLe8D9-eBwwvQqNNMsh99/view?usp=sharing",
            "CAUSA ACEVICHADA NORTENA": "https://drive.google.com/file/d/1-_FHzh7nCyUuKg0a4OQW5pYcw1KekU7c/view?usp=sharing",
            "CAUSA CARRETILLERA": "https://drive.google.com/file/d/1jYm98IAVsnLnoHZ2bspDzA8-pjeJXPqS/view?usp=sharing",
            "CAUSA DE LANGOSTINOS": "https://drive.google.com/file/d/1PZ_ranfFskKxIKJWu4S_B5bJayetpuSY/view?usp=sharing",
            "TRIO CAUSERO": "https://drive.google.com/file/d/1b55LxE19x947NLQty-FF6eGdMv-kZZ9M/view?usp=sharing",
            "CAUSA DE CANGREJO ACEVICHADA": "https://drive.google.com/file/d/1W4hdy1zz8WQ5-u3DXJlnw7p9on3Cbd5Q/view?usp=sharing",
            "CAUSA DE PESCADO": "https://drive.google.com/file/d/1u9myGB5Q4CDnyBvjR6SZ1d91YvXmGXJm/view?usp=sharingg",
            "CAUSA DE LOMO SALTADO": "https://drive.google.com/file/d/11VFQnoDFQzUTiqiYX2MXlIVcifYosEbQ/view?usp=sharing",
            "CAUSA DE LOMO FINO": "https://drive.google.com/file/d/107MTUjtrlpK5Wbwxo-c0k1nr-fABYrLF/view?usp=sharing",
            "CAUSA DE POLLO 30 PORC": "https://drive.google.com/file/d/1dGJGUCRprCtRqJCFnxL6XBHqCOXcb47-/view?usp=sharing",
            
            # PIQUEOS (faltan imgenes)
            "TAMAL VERDE NORTENO": "https://drive.google.com/file/d/1NmPHg7MX2PQ2g8p_iFR4I7ggbASQ2ohy/view?usp=sharing",
            "WANTAN DE PESCADO": "https://drive.google.com/file/d/1Qhdcy2gadnTbbXwhMz-oDWg_dvgiqU09/view?usp=sharing",
            "CHOROS A LA CHALACA": "https://drive.google.com/file/d/1gvtcBrxAE1HRr_vjeq2-iXSaoe33f-_h/view?usp=sharing",
            "PULPO AL OLIVO": "https://drive.google.com/file/d/1CzjRGucUTPDq1Y7VXMKMxUoeZ5QcD-Gc/view?usp=sharing",
            "CONCHAS A LA CHALACA": "https://drive.google.com/file/d/1sZA6iGMCzTDPAEysUtURx3-JFaCuV6pC/view?usp=sharing",
            "CONCHAS A LA PARMESANA": "https://drive.google.com/file/d/1HF_7ruoLqLt9uMPMvj6wUErh6Y-Zh2vg/view?usp=sharing",
            "PIQUEO BARRA ARENA": "https://drive.google.com/file/d/1Mj340DCFnB5kSB_DbYNp5YneCGxlhULS/view?usp=sharing",
            "5 und conchas a la parmesana": "https://drive.google.com/file/d/1AOW8uy_Kn3hiWQA7g3aL6VXbQXMOTWOd/view?usp=sharing",
            "CONCHAS AL AJI AMARILLO": "https://drive.google.com/file/d/1aFCR_LNtOv-cxdOufvBXkqFX4h8hMpDT/view?usp=sharing",
            "LANGOSTINOS AL AJILLO": "https://drive.google.com/file/d/1TNES599lqtSkWt13NAu1Q-3s08w2RUzP/view?usp=sharing",
            "TORTITAS DE CHOCLO": "https://drive.google.com/file/d/1YlRzG7Eh4yjuHcnYL53rXeI7njyjhsk6/view?usp=sharing",
            "MARISCOS A LA CHALACA": "https://drive.google.com/file/d/1elCSo_i9mMbl7FY9npufp2qoVrRNg2cY/view?usp=sharing",
            
            # LECHE DE TIGRE (faltan imgenes)
            "LECHE DE TIGRE": "https://drive.google.com/file/d/1Ci_Ujn_DUZdYcT0yDF6Ms7O3aXn1pEUL/view?usp=sharing",
            "LECHE CARRETILLERA": "https://drive.google.com/file/d/1b55LxE19x947NLQty-FF6eGdMv-kZZ9M/view?usp=sharing",
            "LECHE DE PANTERA": "https://drive.google.com/file/d/1vxvWPvGLpek4IULJSPGVerSskJs38sI9/view?usp=sharing",
            "LECHE DE MARISCOS": "https://drive.google.com/file/d/1JmJCPjmPzwjl4M9_rk60u1FcOh_CLF0e/view?usp=sharing",
            "LECHE BARRA ARENA": "https://drive.google.com/file/d/1b55LxE19x947NLQty-FF6eGdMv-kZZ9M/view?usp=sharing",
            
            # TACU TACU (faltan imgenes)
            "TACU TACU DE PESCADO FRITO": "",
            "TACU TACU DE PESCADO A LA PLANCHA": "",
            "TACU TACU DE MARISCOS": "",
            "TACU TACU DE LOMO SALTADO": "",
            "TACU TACU DE LOMO FINO": "",
            "TACU TACU A LO MACHO": "",
            
            # SOPAS (faltan imgenes)
            "CHILCANITO DE PESCADO": "",
            "CHUPE DE PESCADO": "",
            "SUDADO DE FILETE DE PESCADO": "",
            "PARIHUELA DE MARISCOS": "",
            "PARIHUELA MIXTA": "",
            "SUDADO DE CONCHAS NEGRAS": "",
            "SUDADO DE CHITA ENTERA": "",
            "AGUADITO DE MARISCOS": "",
            
            # DUO MARINO (faltan imgenes)
            "DUO CARRETILLERO": "https://drive.google.com/file/d/1nVCbCj6U7cjF-jQqYfY05CHDPSUJx7f1/view?usp=sharing",
            "DUO BARRA ARENA": "https://drive.google.com/file/d/1nVCbCj6U7cjF-jQqYfY05CHDPSUJx7f1/view?usp=sharing",
            
            # TRIO MARINO (faltan imgenes)
            "TRIO MARINO": "https://drive.google.com/file/d/1NH3M9iey30HGYW4y5iqx4QDEpoUBguGu/view?usp=sharing",
            
            # PROMOCIONES (faltan imgenes)
            "PROMOCION CEVICHE + CHICHARRON": "",
            "PROMOCION CEVICHE + ARROZ": "",
            
            # RONDA MARINA (faltan imgenes)
            "RONDA MARINA CLASICA": "",
            "RONDA MARINA PREMIUM": "",
            
            # BEBIDAS CON ALCOHOL (ya tienen imagen los siguientes)
            "PISCO SOUR": "https://drive.google.com/file/d/1V5NGG5U4HCbPTEOZkC3UC8OZQlQLSrlQ/view?usp=sharing",
            "CHILCANO DE PISCO": "https://drive.google.com/file/d/1QlMnH9bRnnJGrZT6MU8Yj2ddOkl9knKK/view?usp=sharing",
            
            # BEBIDAS CON ALCOHOL (faltan imgenes)
            "CHILCANO DE MARACUYA": "",
            "ALGARROBINA": "",
            "MARACUYA SOUR": "",
            
            # BEBIDAS SIN ALCOHOL (ya tienen imagen los siguientes)
            "CHICHA MORADA": "https://drive.google.com/file/d/1_w-Wk393ouoSeZdlkSLrWGbNMA7N61xj/view?usp=sharing",
            "LIMONADA FROZEN": "https://drive.google.com/file/d/1fbXhbre-TzuqinCYw5637T375-a8f1Go/view?usp=sharing",
            "INCA KOLA 1.5L": "https://drive.google.com/file/d/14KIxsU03UQhq80ijLqdEDJXB0HLgLqr7/view?usp=sharing",
            "INCA KOLA": "https://drive.google.com/file/d/14KIxsU03UQhq80ijLqdEDJXB0HLgLqr7/view?usp=sharing",
            "AGUA MINERAL SAN LUIS": "https://drive.google.com/file/d/1yJ9gMthGnBnaV6kXLM7pENmiFT5K5u3Z/view?usp=sharing",
            
            # BEBIDAS SIN ALCOHOL (faltan imgenes)
            "LIMONADA CLASICA": "https://drive.google.com/file/d/1fbXhbre-TzuqinCYw5637T375-a8f1Go/view?usp=sharing",
            "LIMONADA DE HIERBA BUENA": "https://drive.google.com/file/d/1fbXhbre-TzuqinCYw5637T375-a8f1Go/view?usp=sharing",
            "CHICHA MORADA NATURAL": "",
            "MARACUYA": "",
            "COCA COLA": "",
            "SPRITE": "",
            "FANTA": "",
            "AGUA SAN LUIS": "",
            
            # POSTRES (ya tienen imagen los siguientes)
            "SUSPIRO LIMENO": "https://drive.google.com/file/d/156YIcyAetJUtoqk-8b07LWETKNdjp4IO/view?usp=sharing",
            "MAZAMORRA MORADA": "https://drive.google.com/file/d/1rXynhqY70wt9UNn0haszs2y0s_5Me6ZF/view?usp=sharing",
            "PICARONES": "https://drive.google.com/file/d/1SnEdVTnPECzLKSRwnEHuErbMPDAHFi5h/view?usp=sharing",
            "CREMA VOLTEADA": "https://drive.google.com/file/d/1WxJ46tSOhXDVaVi92_4NRx5lk5NHc80e/view?usp=sharing",
            
            # ADICIONALES (faltan imgenes)
            "CAMOTE": "",
            "CHOCLO": "",
            "YUCA": "",
            "CANCHA": "",
            "YUQUITAS FRITAS": "",
            
            # PORCIONES (faltan imgenes)
            "PORCION DE ARROZ": "",
            "PORCION DE PAPAS FRITAS": "",
            "PORCION DE ENSALADA": "",
            
            # BAR ARENA (faltan imgenes)
            "COCTEL ESPECIAL": "",
            "SANGRIA": "",
            
            # PESCADOS ENTEROS (faltan imgenes)
            "CHITA FRITA": "",
            "CORVINA FRITA": "",
            "LENGUADO FRITO": "",
            
            # CRIOLLO (faltan imgenes)
            "LOMO SALTADO": "",
            "AJI DE GALLINA": "",
            "SECO DE CABRITO": "",
            
            # CHILCANOS PRECIO NORMAL (faltan imgenes)
            "CHILCANO CLASICO": "",
            "CHILCANO DE MARACUYA NORMAL": "",
            
            # MAKIS Y ALITAS (faltan imgenes)
            "MAKI DE LANGOSTINOS": "https://drive.google.com/file/d/1NxiGRZw3di91BCuxzEJv6xAmhj4r5H6A/view?usp=sharing",
            "MAKI ACEVICHADO": "https://drive.google.com/file/d/1NxiGRZw3di91BCuxzEJv6xAmhj4r5H6A/view?usp=sharing",
            "ALITAS BROASTER": "https://drive.google.com/file/d/15JROipoRmMIDj-YKO8Sc5UcZmi8kZKyU/view?usp=sharing",
        }
        
        # ==================== MAPEO DE IMGENES DE CATEGORAS ====================
        categorias_seed_imagenes = {
            # Categoras con imagen
            "CEVICHES": "https://drive.google.com/file/d/1ZaYA_c1ZGfl6tsPe80-fwSzpHR_LYzSZ/view?usp=sharing",
            "TIRADITOS": "https://drive.google.com/file/d/10xFfoYsezQRTC3EvLKm28BJGnImhAJjO/view?usp=sharing",
            "CHICHARRONES": "https://drive.google.com/file/d/1qdabG7kbNr86IpRQALOw1mgQDxBRTnsC/view?usp=sharing",
            "ARROCES": "https://drive.google.com/file/d/14xM_kLEcGtsOORHEp5MCDMCJIGgzs45J/view?usp=sharing",
            "CAUSAS": "https://drive.google.com/file/d/1kRcHUgMqWTHDEX5XVUYNlGPTnkMOQRsa/view?usp=sharing",
            "BEBIDAS": "https://drive.google.com/file/d/1AhNWmlJwuWb0XzXV8Zjs0xD2ZPHT6jzm/view?usp=sharing",
            "POSTRES": "https://drive.google.com/file/d/1gxaT1PCMx1lQ-Hvcug9ujWr3RnVK3WPd/view?usp=sharing",
            
            # Categoras sin imagen (agregar URLs despus)
            "PIQUEOS": "https://drive.google.com/file/d/1p-sCs6-LuOXhmGNDNcjJ7xMn84kk0PWA/view?usp=sharing",
            "LECHE DE TIGRE": "https://drive.google.com/file/d/1Ci_Ujn_DUZdYcT0yDF6Ms7O3aXn1pEUL/view?usp=sharing",
            "ARROZ": "https://drive.google.com/file/d/1spMKGOWCTLbjI1jSXg95MceV5xb5M7cT/view?usp=sharing",
            "TACU TACU": "https://drive.google.com/file/d/12zU5d9MgOFY1tRjurnOMZ-QR38I-RHo2/view?usp=sharing",
            "SOPAS": "https://drive.google.com/file/d/127Vv8P18h1cZ6G6X5l6Cv6sRQdJJbew3/view?usp=sharing",
            "TIRADITO": "https://drive.google.com/file/d/1XEkm66yVz95ctKVeKDxhDT00ghRaWTsD/view?usp=sharing",
            "CHICHARRON": "https://drive.google.com/file/d/1qdabG7kbNr86IpRQALOw1mgQDxBRTnsC/view?usp=sharing",
            "DUO MARINO": "https://drive.google.com/file/d/1WxJ46tSOhXDVaVi92_4NRx5lk5NHc80e/view?usp=sharing",
            "TRIO MARINO": "https://drive.google.com/file/d/1NH3M9iey30HGYW4y5iqx4QDEpoUBguGu/view?usp=sharing",
            "PROMOCIONES": "https://drive.google.com/file/d/1J_V9gwOdKJK9VTiCxtyXqvji_tU8gUzn/view?usp=sharing",
            "RONDA MARINA": "https://drive.google.com/file/d/1UMcWZiq_-XMicbaPUoYzQVhadjw6jQF2/view?usp=sharing",
            "BEBIDAS CON ALCOHOL": "https://drive.google.com/file/d/1DC60g10NriP0GJi6xExHn7bODsoen-DZ/view?usp=sharing",
            "BEBIDAS SIN ALCOHOL": "https://drive.google.com/file/d/10k3cw073DyCS37uq3zyfI9AvFso5EZe9/view?usp=sharing",
            "adicionales": "https://drive.google.com/file/d/1iw3mybv70s_ihUbqkzzk6qAfkEogU3aL/view?usp=sharing",
            "PORCIONES": "",
            "BAR ARENA": "",
            "CONSUMO": "https://drive.google.com/file/d/1oHxDCheRX92vZk7HlUS3iBpgL1qFi2Yz/view?usp=sharing",
            "PESCADOS ENTEROS": "",
            "CRIOLLO": "",
            "CHILCANOS PRECIO NORMAL": "",
            "MAKIS Y ALITAS": "https://drive.google.com/file/d/1MEkKCJuwHUoXyIyHWsidNAy2RzoTxxs6/view?usp=sharing",
        }
        
        # ==================== ACTUALIZAR IMGENES DE PRODUCTOS ====================
        print("\n Actualizando imgenes de productos...")
        productos_actualizados = 0
        productos_con_imagen_previa = 0
        productos_no_encontrados = []
        
        for nombre_key, producto in self.productos_existentes.items():
            if nombre_key in productos_seed_imagenes:
                imagen_url = productos_seed_imagenes[nombre_key]
                
                #  SOLO actualizar si la URL NO est vaca y el producto NO tiene imagen
                if imagen_url and imagen_url.strip():  # Filtrar URLs vacas
                    if not producto.imagen_path:
                        producto.imagen_path = imagen_url
                        self.session.add(producto)
                        productos_actualizados += 1
                        print(f"    {producto.nombre:<45}  Imagen agregada")
                    else:
                        productos_con_imagen_previa += 1
                        print(f"    {producto.nombre:<45}  Ya tiene imagen, skip")
                # Si la URL est vaca, lo tratamos como "no encontrado"
                elif not producto.imagen_path:
                    productos_no_encontrados.append(producto.nombre)
            else:
                # Producto real NO tiene imagen en seed
                if not producto.imagen_path:
                    productos_no_encontrados.append(producto.nombre)
        
        await self.session.commit()
        
        print(f"\n    {productos_actualizados} productos actualizados con imgenes")
        if productos_con_imagen_previa > 0:
            print(f"    {productos_con_imagen_previa} productos ya tenan imagen (sin cambios)")
        
        if productos_no_encontrados:
            print(f"\n     {len(productos_no_encontrados)} productos SIN imagen en seed:")
            for i, nombre in enumerate(productos_no_encontrados[:10], 1):  # Mostrar solo primeros 10
                print(f"      {i}. {nombre}")
            if len(productos_no_encontrados) > 10:
                print(f"      ... y {len(productos_no_encontrados) - 10} ms")
        
        # ==================== ACTUALIZAR IMGENES DE CATEGORAS ====================
        print("\n Actualizando imgenes de categoras...")
        categorias_actualizadas = 0
        categorias_con_imagen_previa = 0
        
        for nombre_key, categoria in self.categorias_existentes.items():
            if nombre_key in categorias_seed_imagenes:
                imagen_url = categorias_seed_imagenes[nombre_key]
                
                #  SOLO actualizar si la URL NO est vaca y la categora NO tiene imagen
                if imagen_url and imagen_url.strip():  # Filtrar URLs vacas
                    if not categoria.imagen_path:
                        categoria.imagen_path = imagen_url
                        self.session.add(categoria)
                        categorias_actualizadas += 1
                        print(f"    {categoria.nombre:<30}  Imagen agregada")
                    else:
                        categorias_con_imagen_previa += 1
                        print(f"    {categoria.nombre:<30}  Ya tiene imagen, skip")
        
        await self.session.commit()
        
        print(f"\n    {categorias_actualizadas} categoras actualizadas con imgenes")
        if categorias_con_imagen_previa > 0:
            print(f"    {categorias_con_imagen_previa} categoras ya tenan imagen (sin cambios)")
        print("="*70 + "\n")

    async def populate_local_catalog_intermediate_tables(self):
        """
        ✨ PASO 8: Poblar tablas intermedias de catálogo multi-local.

        Activa TODOS los items existentes para el local creado:
        - Todas las categorías
        - Todos los productos
        - Todos los tipos de opciones
        - Todas las opciones de productos
        """
        print("\n" + "="*70)
        print(" ✨ POBLANDO TABLAS INTERMEDIAS DE CATÁLOGO MULTI-LOCAL")
        print("="*70)

        if not self.local:
            print("   ⚠️  ERROR: No hay local creado. Abortando población.")
            return

        print(f"   📍 Local: {self.local.nombre} (ID: {self.local.id})")

        # ==================== ACTIVAR TODAS LAS CATEGORÍAS ====================
        print("\n 📂 Activando todas las categorías para el local...")

        result = await self.session.execute(select(CategoriaModel))
        categorias = result.scalars().all()

        count_categorias = 0
        for categoria in categorias:
            # Verificar si ya existe la relación
            existing = await self.session.execute(
                select(LocalesCategoriasModel).where(
                    LocalesCategoriasModel.id_local == self.local.id,
                    LocalesCategoriasModel.id_categoria == categoria.id
                )
            )
            if not existing.scalars().first():
                relacion = LocalesCategoriasModel(
                    id_local=self.local.id,
                    id_categoria=categoria.id,
                    activo=True,
                    orden_override=None  # Usar orden original
                )
                self.session.add(relacion)
                count_categorias += 1

        await self.session.commit()
        print(f"    ✅ {count_categorias} categorías activadas")

        # ==================== ACTIVAR TODOS LOS PRODUCTOS ====================
        print("\n 🍽️  Activando todos los productos para el local...")

        result = await self.session.execute(select(ProductoModel))
        productos = result.scalars().all()

        count_productos = 0
        for producto in productos:
            # Verificar si ya existe la relación
            existing = await self.session.execute(
                select(LocalesProductosModel).where(
                    LocalesProductosModel.id_local == self.local.id,
                    LocalesProductosModel.id_producto == producto.id
                )
            )
            if not existing.scalars().first():
                relacion = LocalesProductosModel(
                    id_local=self.local.id,
                    id_producto=producto.id,
                    activo=True,
                    # Sin overrides inicialmente (NULL = usar valores originales)
                    precio_override=None,
                    disponible_override=None,
                    nombre_override=None,
                    descripcion_override=None
                )
                self.session.add(relacion)
                count_productos += 1

        await self.session.commit()
        print(f"    ✅ {count_productos} productos activados")

        # ==================== ACTIVAR TODOS LOS TIPOS DE OPCIONES ====================
        print("\n 🔧 Activando todos los tipos de opciones para el local...")

        result = await self.session.execute(select(TipoOpcionModel))
        tipos_opciones = result.scalars().all()

        count_tipos = 0
        for tipo_opcion in tipos_opciones:
            # Verificar si ya existe la relación
            existing = await self.session.execute(
                select(LocalesTiposOpcionesModel).where(
                    LocalesTiposOpcionesModel.id_local == self.local.id,
                    LocalesTiposOpcionesModel.id_tipo_opcion == tipo_opcion.id
                )
            )
            if not existing.scalars().first():
                relacion = LocalesTiposOpcionesModel(
                    id_local=self.local.id,
                    id_tipo_opcion=tipo_opcion.id,
                    activo=True
                )
                self.session.add(relacion)
                count_tipos += 1

        await self.session.commit()
        print(f"    ✅ {count_tipos} tipos de opciones activados")

        # ==================== ACTIVAR TODAS LAS OPCIONES DE PRODUCTOS ====================
        print("\n ⚙️  Activando todas las opciones de productos para el local...")

        result = await self.session.execute(select(ProductoOpcionModel))
        productos_opciones = result.scalars().all()

        count_opciones = 0
        for producto_opcion in productos_opciones:
            # Verificar si ya existe la relación
            existing = await self.session.execute(
                select(LocalesProductosOpcionesModel).where(
                    LocalesProductosOpcionesModel.id_local == self.local.id,
                    LocalesProductosOpcionesModel.id_producto_opcion == producto_opcion.id
                )
            )
            if not existing.scalars().first():
                relacion = LocalesProductosOpcionesModel(
                    id_local=self.local.id,
                    id_producto_opcion=producto_opcion.id,
                    activo=True,
                    # Sin override de precio inicialmente (NULL = usar precio adicional original)
                    precio_adicional_override=None
                )
                self.session.add(relacion)
                count_opciones += 1

        await self.session.commit()
        print(f"    ✅ {count_opciones} opciones de productos activadas")

        print(f"\n{'='*70}")
        print(f" ✨ POBLACIÓN DE CATÁLOGO MULTI-LOCAL COMPLETADA")
        print(f"{'='*70}")
        print(f"    📂 Categorías activadas: {count_categorias}")
        print(f"    🍽️  Productos activados: {count_productos}")
        print(f"    🔧 Tipos de opciones activados: {count_tipos}")
        print(f"    ⚙️  Opciones de productos activadas: {count_opciones}")
        print(f"{'='*70}\n")

    async def enrich_all(self):
        """
         Ejecuta todos los pasos de enriquecimiento.
        """
        print("\n" + "="*70)
        print(" INICIANDO ENRIQUECIMIENTO DE DATOS EXISTENTES")
        print("="*70)
        print("     NO se crearn productos ni categoras nuevas")
        print("    Solo se agregar informacin complementaria")
        print("="*70)

        # PASO 0: Crear Local (las Zonas y Mesas se crean via POST /sync/mesas)
        await self.create_local()
        await self.session.commit()

        # Cargar datos existentes (solo consulta, no crea)
        await self.load_existing_data()

        # PASO 2: Crear alrgenos
        await self.create_alergenos()

        # PASO 3: Crear tipos de opciones
        await self.create_tipos_opciones()
        
        # PASO 4: Asociar alrgenos a productos
        await self.associate_alergenos_to_productos()
        
        # PASO 5: Crear opciones para productos
        await self.create_opciones_for_productos()

        # PASO 6: Crear roles si no existen (ELIMINADO - Ya no se usan roles)
        # await self.create_roles_if_not_exist()

        # PASO 7: Actualizar imgenes desde seed (NUEVO)
        await self.update_images_from_seed()

        # PASO 8: Poblar tablas intermedias de catálogo multi-local
        await self.populate_local_catalog_intermediate_tables()

        print("\n" + "="*70)
        print(" ENRIQUECIMIENTO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"    Productos procesados: {len(self.productos_existentes)}")
        print(f"     Alrgenos creados: {len(self.alergenos)}")
        print(f"     Tipos de opciones creados: {len(self.tipos_opciones)}")
        print("="*70 + "\n")


async def main():
    """Funcin principal."""
    database_url = get_database_url()
    
    print("\n" + "="*70)
    print(" CONFIGURACIN DE BASE DE DATOS")
    print("="*70)
    print(f"   URL: {database_url}")
    print("="*70)
    
    # Crear engine y sesin
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        enricher = DataEnricher(session)
        await enricher.enrich_all()
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
