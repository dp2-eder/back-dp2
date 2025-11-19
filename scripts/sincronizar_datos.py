"""
Script para sincronizar datos automáticamente con el backend.

Ejecuta:
1. Transformación del JSON si es necesario
2. Sincronización de productos (/api/v1/sync/platos)
3. Enriquecimiento de datos (/api/v1/sync/enrich)
"""
import asyncio
import httpx
import json
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def sincronizar():
    """Ejecuta el flujo completo de sincronización."""
    
    print("🔄 INICIANDO SINCRONIZACIÓN DE DATOS")
    print("="*70)
    
    # Verificar que el servidor esté corriendo
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print(" ERROR: El servidor no está disponible")
                print(f"   Respuesta: {response.status_code}")
                return
    except Exception as e:
        print(f"❌ ERROR: No se puede conectar con el servidor en {BASE_URL}")
        print(f"   Asegúrate de que uvicorn esté corriendo")
        print(f"   Error: {e}")
        return
    
    print("✅ Servidor disponible\n")
    
    # PASO 1: Verificar/transformar JSON
    scripts_dir = Path(__file__).parent
    json_path = scripts_dir / "platos_domotica.json"
    
    if not json_path.exists():
        print("⚠️  platos_domotica.json no existe. Generando...")
        from transform_json_for_sync import transform_platos_json
        transform_platos_json()
        print()
    
    # PASO 2: Sincronizar productos
    print("📦 PASO 1: Sincronizando productos...")
    print("-"*70)
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            productos_data = json.load(f)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v1/sync/platos",
                json=productos_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Productos sincronizados exitosamente")
                print(f"   Categorías creadas: {result['resultados']['categorias_creadas']}")
                print(f"   Productos creados: {result['resultados']['productos_creados']}")
                print(f"   Productos actualizados: {result['resultados']['productos_actualizados']}")
                print(f"   Productos desactivados: {result['resultados']['productos_desactivados']}")
            else:
                print(f"❌ Error al sincronizar productos: {response.status_code}")
                print(f"   Detalle: {response.text}")
                return
    
    except Exception as e:
        print(f"❌ Error durante la sincronización de productos: {e}")
        return
    
    print()
    
    # PASO 3: Enriquecer datos
    print("✨ PASO 2: Enriqueciendo datos (alérgenos, opciones, relaciones)...")
    print("-"*70)
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:  # Timeout más largo
            response = await client.post(f"{BASE_URL}/api/v1/sync/enrich")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Datos enriquecidos exitosamente")
                print(f"   Productos procesados: {result['data']['productos_procesados']}")
                print(f"   Alérgenos creados: {result['data']['alergenos_creados']}")
                print(f"   Alérgenos totales: {result['data']['alergenos_totales']}")
                print(f"   Tipos opciones creados: {result['data']['tipos_opciones_creados']}")
                print(f"   Tipos opciones totales: {result['data']['tipos_opciones_totales']}")
            else:
                print(f"❌ Error al enriquecer datos: {response.status_code}")
                print(f"   Detalle: {response.text}")
                return
    
    except Exception as e:
        print(f"❌ Error durante el enriquecimiento: {e}")
        return
    
    print()
    print("="*70)
    print("🎉 SINCRONIZACIÓN COMPLETADA EXITOSAMENTE")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(sincronizar())
