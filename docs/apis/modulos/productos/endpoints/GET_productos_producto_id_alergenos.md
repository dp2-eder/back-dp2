# GET /productos/{producto_id}/alergenos

> **⭐ Obtener alérgenos de un producto específico**

## META

- **Host Producción:** `https://back-dp2.onrender.com`
- **Host Local:** `http://127.0.0.1:8000`
- **Path:** `/api/v1/productos/{producto_id}/alergenos`
- **Método:** `GET`
- **Autenticación:** No requerida

## DESCRIPCIÓN

Obtiene todos los alérgenos asociados a un producto específico. Este endpoint es esencial para mostrar información de alérgenos en el menú y alertar a clientes con alergias alimentarias.

**Casos de uso:**
- ✅ Mostrar advertencias de alérgenos en el menú
- ✅ Filtrar productos según alergias del cliente
- ✅ Información nutricional y de seguridad alimentaria

## ENTRADA

### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `producto_id` | `string` | ID ULID del producto (requerido) |

### Headers

Ningún header especial requerido.

### Query Parameters

Ningún parámetro de consulta.

## SALIDA

### Success Response (200 OK)

```json
[
  {
    "id": "01J9ALER123ABCDEFGHIJKLMN",
    "nombre": "Gluten",
    "descripcion": "Proteína presente en trigo, cebada, centeno y avena",
    "icono": "🌾",
    "nivel_riesgo": "ALTO",
    "fecha_creacion": "2025-10-28T10:00:00Z",
    "fecha_modificacion": "2025-10-28T10:00:00Z",
    "creado_por": null,
    "modificado_por": null
  },
  {
    "id": "01J9ALER456ABCDEFGHIJKLMN",
    "nombre": "Mariscos",
    "descripcion": "Crustáceos y moluscos marinos",
    "icono": "🦐",
    "nivel_riesgo": "CRITICO",
    "fecha_creacion": "2025-10-28T10:00:00Z",
    "fecha_modificacion": "2025-10-28T10:00:00Z",
    "creado_por": null,
    "modificado_por": null
  }
]
```

### Diccionario de Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `string` | ID ULID del alérgeno |
| `nombre` | `string` | Nombre del alérgeno (ej: "Gluten", "Lactosa") |
| `descripcion` | `string` | Descripción detallada del alérgeno |
| `icono` | `string` | Emoji o representación visual |
| `nivel_riesgo` | `enum` | Nivel de riesgo: `BAJO`, `MEDIO`, `ALTO`, `CRITICO` |
| `fecha_creacion` | `datetime` | Timestamp de creación |
| `fecha_modificacion` | `datetime` | Timestamp de última modificación |
| `creado_por` | `string/null` | Usuario que creó el registro |
| `modificado_por` | `string/null` | Usuario que modificó por última vez |

### Response Vacía (200 OK)

Si el producto no tiene alérgenos asociados:

```json
[]
```

## ERRORES

### 400 Bad Request

```json
{
  "type": "validation_error",
  "title": "Parámetros inválidos",
  "detail": "El ID del producto no es válido",
  "status": 400
}
```

### 404 Not Found

```json
{
  "type": "not_found",
  "title": "Producto no encontrado",
  "detail": "No se encontró el producto con ID 01J9PROD123ABCDEFGHIJKLMN",
  "status": 404
}
```

### 500 Internal Server Error

```json
{
  "type": "internal_error",
  "title": "Error interno del servidor",
  "detail": "Error interno del servidor: Database connection failed",
  "status": 500
}
```

## EJEMPLOS

### Ejemplo 1: Producto con Alérgenos

**Request:**
```bash
curl -X GET "https://back-dp2.onrender.com/api/v1/productos/01J9CEVI123ABCDEFGHIJKLMN/alergenos"
```

**Response (200):**
```json
[
  {
    "id": "01J9ALER123ABCDEFGHIJKLMN",
    "nombre": "Mariscos",
    "descripcion": "Crustáceos y moluscos marinos que pueden causar reacciones alérgicas severas",
    "icono": "🦐",
    "nivel_riesgo": "CRITICO",
    "fecha_creacion": "2025-10-28T15:30:00Z",
    "fecha_modificacion": "2025-10-28T15:30:00Z",
    "creado_por": null,
    "modificado_por": null
  },
  {
    "id": "01J9ALER456ABCDEFGHIJKLMN",
    "nombre": "Sulfitos",
    "descripcion": "Conservantes que pueden causar reacciones en personas sensibles",
    "icono": "⚠️",
    "nivel_riesgo": "MEDIO",
    "fecha_creacion": "2025-10-28T15:30:00Z",
    "fecha_modificacion": "2025-10-28T15:30:00Z",
    "creado_por": null,
    "modificado_por": null
  }
]
```

### Ejemplo 2: Producto sin Alérgenos

**Request:**
```bash
curl -X GET "https://back-dp2.onrender.com/api/v1/productos/01J9AGUA123ABCDEFGHIJKLMN/alergenos"
```

**Response (200):**
```json
[]
```

### Ejemplo 3: Producto No Existe

**Request:**
```bash
curl -X GET "https://back-dp2.onrender.com/api/v1/productos/01J9NOEXISTE123456789/alergenos"
```

**Response (404):**
```json
{
  "type": "not_found",
  "title": "Producto no encontrado",
  "detail": "No se encontró el producto con ID 01J9NOEXISTE123456789",
  "status": 404
}
```

## CASOS DE USO

### 1. Menú con Advertencias de Alérgenos

```javascript
// Frontend: Mostrar advertencias en el menú
const producto = await fetch(`/api/v1/productos/${productoId}`);
const alergenos = await fetch(`/api/v1/productos/${productoId}/alergenos`);

if (alergenos.length > 0) {
  const alertas = alergenos
    .filter(a => a.nivel_riesgo === 'CRITICO')
    .map(a => `${a.icono} ${a.nombre}`)
    .join(', ');
  
  console.log(`⚠️ CONTIENE: ${alertas}`);
}
```

### 2. Filtro por Alergias del Cliente

```javascript
// Filtrar productos seguros para un cliente
const clienteAlergias = ['01J9ALER123...', '01J9ALER456...']; // IDs de alergenos

async function esProductoSeguro(productoId) {
  const alergenos = await fetch(`/api/v1/productos/${productoId}/alergenos`);
  const alergenosIds = alergenos.map(a => a.id);
  
  // Verificar si hay intersección con alergias del cliente
  return !clienteAlergias.some(alergia => alergenosIds.includes(alergia));
}
```

### 3. Dashboard de Gestión

```javascript
// Contar productos por nivel de riesgo de alérgenos
async function estadisticasAlergenos(productos) {
  const stats = { CRITICO: 0, ALTO: 0, MEDIO: 0, BAJO: 0 };
  
  for (const producto of productos) {
    const alergenos = await fetch(`/api/v1/productos/${producto.id}/alergenos`);
    const maxRiesgo = Math.max(...alergenos.map(a => getRiesgoLevel(a.nivel_riesgo)));
    stats[getRiesgoName(maxRiesgo)]++;
  }
  
  return stats;
}
```

## NIVELES DE RIESGO

| Nivel | Descripción | Ejemplos |
|-------|-------------|----------|
| `CRITICO` | Alérgenos que pueden causar reacciones severas | Mariscos, Frutos secos, Huevos |
| `ALTO` | Alérgenos comunes que afectan a muchas personas | Gluten, Lactosa, Soja |
| `MEDIO` | Alérgenos con reacciones moderadas | Sulfitos, Colorantes |
| `BAJO` | Sensibilidades menores | Algunos aditivos |

## URLs COMPLETAS

### Producción
```
GET https://back-dp2.onrender.com/api/v1/productos/{producto_id}/alergenos
```

### Local
```
GET http://127.0.0.1:8000/api/v1/productos/{producto_id}/alergenos
```

## INTEGRACIÓN CON OTROS ENDPOINTS

### Flujo Completo: Información de Producto

```bash
# 1. Obtener información básica del producto
GET /api/v1/productos/{producto_id}

# 2. Obtener opciones disponibles
GET /api/v1/productos/{producto_id}/opciones

# 3. Obtener alérgenos (este endpoint)
GET /api/v1/productos/{producto_id}/alergenos

# 4. Crear pedido con información completa
POST /api/v1/pedidos/completo
```

## NOTAS TÉCNICAS

- ⚡ **Performance:** Endpoint optimizado con JOIN directo a tabla de alérgenos
- 🔄 **Cache-friendly:** Los alérgenos de un producto cambian raramente
- ✅ **Siempre retorna array:** Incluso si no hay alérgenos (array vacío)
- 🚨 **Seguridad:** Información crítica para la salud del cliente
