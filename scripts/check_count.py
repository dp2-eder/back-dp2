import json

with open('scripts/platos_domotica.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f'Total productos en platos_domotica.json: {len(data)}')

with open('scripts/platos.json', 'r', encoding='utf-8') as f:
    original = json.load(f)
    print(f'Total productos en platos.json original: {len(original["items"])}')
