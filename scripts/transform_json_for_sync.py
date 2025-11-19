"""
Script para transformar los JSON existentes al formato esperado por /api/v1/sync/platos

Este script:
1. Lee platos.json (lista de productos sin categoría)
2. Lee categoria.json (lista de categorías)
3. Asigna cada producto a una categoría por defecto
4. Genera un JSON en el formato esperado por el endpoint
"""
import json
from pathlib import Path

def transform_platos_json():
    """
    Transforma platos.json al formato ProductoDomotica[]
    """
    # Leer archivos
    scripts_dir = Path(__file__).parent
    platos_path = scripts_dir / "platos.json"
    categorias_path = scripts_dir / "categoria.json"
    output_path = scripts_dir / "platos_domotica.json"
    
    with open(platos_path, 'r', encoding='utf-8') as f:
        platos_data = json.load(f)
    
    with open(categorias_path, 'r', encoding='utf-8') as f:
        categorias_data = json.load(f)
    
    # Obtener la primera categoría como default (o podrías mapear por nombre)
    categoria_default = categorias_data['items'][0]['nombre'] if categorias_data['items'] else "GENERAL"
    
    # Transformar productos
    productos_domotica = []
    
    for producto in platos_data['items']:
        # Mapeo simple: asignar categoría por nombre de producto
        categoria = asignar_categoria_por_nombre(producto['nombre'])
        
        producto_domotica = {
            "categoria": categoria,
            "nombre": producto['nombre'],
            "stock": "100" if producto.get('disponible', True) else "0",
            "precio": str(producto.get('precio_base', '0.00'))
        }
        productos_domotica.append(producto_domotica)
    
    # Guardar resultado
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(productos_domotica, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Archivo transformado guardado en: {output_path}")
    print(f"   Total de productos: {len(productos_domotica)}")
    return output_path


def asignar_categoria_por_nombre(nombre: str) -> str:
    """
    Asigna una categoría basándose en el nombre del producto.
    """
    nombre_upper = nombre.upper()
    
    # Mapeo por palabras clave
    if any(kw in nombre_upper for kw in ['TAMAL', 'WANTAN', 'CHOROS', 'PULPO', 'CONCHAS', 'LANGOSTINOS', 'TORTITAS', 'MARISCOS A LA']):
        return "PIQUEOS"
    
    if 'LECHE' in nombre_upper:
        return "LECHE DE TIGRE"
    
    if 'CAUSA' in nombre_upper:
        return "CAUSAS"
    
    if any(kw in nombre_upper for kw in ['FILETE', 'CHAUFA', 'ARROZ']):
        return "ARROZ"
    
    if 'TACU TACU' in nombre_upper:
        return "TACU TACU"
    
    if any(kw in nombre_upper for kw in ['CHUPE', 'SUDADO', 'PARIHUELA', 'AGUADITO', 'CHILCANITO']):
        return "SOPAS"
    
    if 'CEVICHE' in nombre_upper:
        return "CEVICHES"
    
    if 'TIRADITO' in nombre_upper:
        return "TIRADITO"
    
    if 'CHICHARRON' in nombre_upper or 'JALEA' in nombre_upper:
        return "CHICHARRON"
    
    if 'DUO MARINO' in nombre_upper:
        return "DUO MARINO"
    
    if 'TRIO' in nombre_upper and 'CAUSERO' not in nombre_upper:
        return "TRIO MARINO"
    
    if any(kw in nombre_upper for kw in ['PROMO', 'PLATO DEL DIA']):
        return "PROMOCIONES"
    
    if 'RONDA' in nombre_upper:
        return "RONDA MARINA"
    
    if any(kw in nombre_upper for kw in ['CHILCANO', 'CERVEZA', 'BEER', 'PILSEN', 'HEINEKEN', 'CORONA']):
        return "BEBIDAS CON ALCOHOL"
    
    # Por defecto
    return "ADICIONALES"


if __name__ == "__main__":
    print("🔄 Transformando platos.json al formato Domotica...")
    output = transform_platos_json()
    print(f"\n📋 Ahora puedes usar {output} para sincronizar con el endpoint")
