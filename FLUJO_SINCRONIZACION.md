# 🔄 Flujo de Sincronización de Datos

## Problema Identificado

Los archivos JSON existentes (`platos.json` y `categoria.json`) tienen una estructura incompatible con el endpoint `/api/v1/sync/platos`:

### ❌ Formato Actual (Incorrecto)
```json
{
  "items": [
    {
      "id": "01K7ZW5WNHT564N3FGXD99N7JT",
      "nombre": "TAMAL VERDE NORTENO",
      "precio_base": "10.00",
      "disponible": true
    }
  ],
  "total": 274
}
```

### ✅ Formato Esperado (Correcto)
```json
[
  {
    "categoria": "PIQUEOS",
    "nombre": "TAMAL VERDE NORTENO",
    "stock": "100",
    "precio": "10.00"
  }
]
```

## Solución Implementada

Se ha creado un script de transformación: `scripts/transform_json_for_sync.py`

Este script:
1. Lee `platos.json`
2. Asigna categorías automáticamente basándose en palabras clave en los nombres
3. Genera `platos_domotica.json` en el formato correcto

## 📋 Pasos para Sincronizar

### 1. Transformar el JSON (Ya hecho)
```bash
python -m scripts.transform_json_for_sync
```

Esto genera: `scripts/platos_domotica.json`

### 2. Sincronizar Productos
Envía una petición POST a `/api/v1/sync/platos` con el contenido de `platos_domotica.json`:

```bash
# Usando curl (PowerShell)
$json = Get-Content scripts\platos_domotica.json -Raw
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/sync/platos" `
  -Method POST `
  -ContentType "application/json" `
  -Body $json
```

O desde tu frontend/Postman:
- **URL**: `POST http://localhost:8000/api/v1/sync/platos`
- **Body**: Contenido de `scripts/platos_domotica.json`
- **Content-Type**: `application/json`

### 3. Enriquecer Datos
Después de sincronizar los productos, ejecuta el enriquecimiento:

```bash
# Petición POST sin body
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/sync/enrich" -Method POST
```

Este paso:
- Crea alérgenos
- Crea tipos de opciones
- Asocia alérgenos a productos
- Crea opciones de productos
- Crea roles
- Actualiza imágenes
- **Pobla las tablas intermedias de catálogo multi-local** (locales_productos, locales_categorias, etc.)

## 🔧 Correcciones Realizadas

### 1. Error en `enrich_existing_data.py`
**Antes:**
```python
if count_productos == 0:
    print("\n ERROR: No hay productos en la BD.")
    sys.exit(1)  # ❌ Mata el servidor
```

**Después:**
```python
if count_productos == 0:
    print("\n ERROR: No hay productos en la BD.")
    raise RuntimeError(  # ✅ Lanza excepción manejable
        "No hay productos en la base de datos. "
        "Ejecuta primero el endpoint /api/v1/sync/platos para sincronizar productos."
    )
```

## 📊 Estado Actual

- ✅ Script de transformación creado
- ✅ JSON transformado generado (100 productos)
- ✅ Error sys.exit() corregido
- ⚠️ El JSON original `platos.json` solo contiene 100 productos de 274 (está truncado)

## 🎯 Notas Importantes

1. **El JSON `platos.json` está incompleto**: Solo tiene 100 productos aunque declara 274
2. **Las categorías se asignan automáticamente** basándose en palabras clave
3. **El orden de ejecución es importante**:
   - Primero `/api/v1/sync/platos`
   - Luego `/api/v1/sync/enrich`
4. **El enriquecimiento crea las relaciones multi-local**: Las tablas `locales_productos`, `locales_categorias`, etc. se populan automáticamente

## 🚀 Alternativa: Usar Script de Seed

Si prefieres empezar desde cero con datos bien estructurados, puedes usar:

```bash
python -m scripts.seed_cevicheria_data
```

Este script crea productos, categorías, alérgenos y opciones completos con datos mock de una cevichería peruana.
