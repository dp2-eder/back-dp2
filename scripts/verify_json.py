import json

with open('scripts/platos.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    items_count = len(data['items'])
    total_declared = data['total']
    
    print(f"Items en el array: {items_count}")
    print(f"Total declarado: {total_declared}")
    print(f"¿Coinciden?: {'✅ Sí' if items_count == total_declared else '❌ No'}")
