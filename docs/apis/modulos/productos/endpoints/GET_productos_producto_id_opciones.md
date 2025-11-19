# GET /productos/{producto_id}/opciones

> **⭐ Obtener producto con sus opciones agrupadas por tipo**

## META

- **Host Producción:** `https://back-dp2.onrender.com`
- **Host Local:** `http://127.0.0.1:8000`
- **Path:** `/api/v1/productos/{producto_id}/opciones`
- **Método:** `GET`
- **Autenticación:** No requerida

## DESCRIPCIÓN

Obtiene los detalles completos de un producto con todas sus opciones **agrupadas por tipo de opción**. Este endpoint es fundamental para mostrar las opciones de personalización disponibles para cada producto en el menú.

**Características:**
- ✅ Información completa del producto (descripción, precio base)
- ✅ Opciones agrupadas por `tipo_opcion` (nivel de picante, acompañamientos, etc.)
- ✅ Metadata de cada tipo (obligatorio, múltiple selección, orden)
- ✅ Precios adicionales por opción

**Casos de uso:**
- 📱 Mostrar opciones de personalización en la app
- 🛒 Construir formulario de pedido con opciones
- 💰 Calcular precios adicionales por opciones seleccionadas

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
{
  "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
  "nombre": "Ceviche Clásico",
  "descripcion": "Pescado fresco del día marinado en limón con cebolla morada, ají amarillo y cilantro",
  "precio_base": "25.00",
  "tipos_opciones": [
    {
      "id_tipo_opcion": "01K7ZE23BCDE6N7OH06QKD4OP7",
      "nombre_tipo": "Nivel de picante",
      "obligatorio": true,
      "multiple_seleccion": false,
      "orden": 1,
      "opciones": [
        {
          "id": "01K7ZF34CDEF7O8PI17RLE5PQ8",
          "nombre": "Sin ají",
          "precio_adicional": "0.00"
        },
        {
          "id": "01K7ZF45DEFG8P9QJ28SMF6QR9",
          "nombre": "Ají suave",
          "precio_adicional": "0.00"
        },
        {
          "id": "01K7ZF56EFGH9Q0RK39TNG7RS0",
          "nombre": "Ají picante",
          "precio_adicional": "2.00"
        }
      ]
    },
    {
      "id_tipo_opcion": "01K7ZG67FGHI0R1SL40UOH8ST1",
      "nombre_tipo": "Acompañamientos",
      "obligatorio": false,
      "multiple_seleccion": true,
      "orden": 2,
      "opciones": [
        {
          "id": "01K7ZH78GHIJ1S2TM51VPI9TU2",
          "nombre": "Camote",
          "precio_adicional": "3.00"
        },
        {
          "id": "01K7ZH89HIJK2T3UN62WQJ0UV3",
          "nombre": "Choclo",
          "precio_adicional": "3.00"
        }
      ]
    }
  ]
}
```

**DICTIONARY (OUTPUT)**

| Field | Data Type | Format | Comment |
|-------|-----------|--------|---------|
| `id` | string | ULID | ID del producto. |
| `nombre` | string | | Nombre del producto. |
| `descripcion` | string | | Descripción del producto. |
| `precio_base` | string | decimal | Precio base sin extras. |
| `tipos_opciones` | array | | Lista de tipos de opciones agrupadas. |
| `tipos_opciones[].id_tipo_opcion` | string | ULID | ID del tipo de opción. |
| `tipos_opciones[].nombre_tipo` | string | | Nombre del tipo (ej: "Nivel de picante"). |
| `tipos_opciones[].obligatorio` | boolean | | Si el cliente debe seleccionar al menos una. |
| `tipos_opciones[].multiple_seleccion` | boolean | | Si puede seleccionar múltiples opciones. |
| `tipos_opciones[].orden` | integer | | Orden de visualización del tipo. |
| `tipos_opciones[].opciones` | array | | Lista de opciones dentro del tipo. |
| `tipos_opciones[].opciones[].id` | string | ULID | ID de la opción. |
| `tipos_opciones[].opciones[].nombre` | string | | Nombre de la opción (ej: "Ají suave"). |
| `tipos_opciones[].opciones[].precio_adicional` | string | decimal | Precio adicional de la opción. |

## ERRORES

| HTTP | Code | Title / Message | Comment |
|------|------|-----------------|---------|
| 404 | `NOT_FOUND` | Recurso no encontrado | Producto no existe. |
| 500 | `INTERNAL_ERROR` | Error interno | Revisar logs. |

## EJEMPLOS

### Ejemplo 1: Producto con Múltiples Tipos de Opciones

**Request:**
```bash
curl -X GET "https://back-dp2.onrender.com/api/v1/productos/01J9CEVI123ABCDEFGHIJKLMN/opciones"
```

**Response (200):**
```json
{
  "id": "01J9CEVI123ABCDEFGHIJKLMN",
  "nombre": "Ceviche Clásico",
  "descripcion": "Pescado fresco del día marinado en limón con cebolla morada, ají amarillo y cilantro",
  "precio_base": "30.00",
  "tipos_opciones": [
    {
      "id_tipo_opcion": "01J9TIPO123ABCDEFGHIJKLMN",
      "nombre_tipo": "Nivel de Picante",
      "obligatorio": true,
      "multiple_seleccion": false,
      "orden": 1,
      "opciones": [
        {
          "id": "01J9OPC123ABCDEFGHIJKLMN",
          "nombre": "Sin ají",
          "precio_adicional": "0.00"
        },
        {
          "id": "01J9OPC456ABCDEFGHIJKLMN",
          "nombre": "Ají suave",
          "precio_adicional": "0.00"
        },
        {
          "id": "01J9OPC789ABCDEFGHIJKLMN",
          "nombre": "Ají picante",
          "precio_adicional": "1.00"
        }
      ]
    },
    {
      "id_tipo_opcion": "01J9TIPO456ABCDEFGHIJKLMN",
      "nombre_tipo": "Acompañamientos",
      "obligatorio": false,
      "multiple_seleccion": true,
      "orden": 2,
      "opciones": [
        {
          "id": "01J9OPC012ABCDEFGHIJKLMN",
          "nombre": "Con choclo",
          "precio_adicional": "3.00"
        },
        {
          "id": "01J9OPC345ABCDEFGHIJKLMN",
          "nombre": "Con camote",
          "precio_adicional": "2.50"
        }
      ]
    }
  ]
}
```

### Ejemplo 2: Producto Sin Opciones

**Request:**
```bash
curl -X GET "https://back-dp2.onrender.com/api/v1/productos/01J9AGUA123ABCDEFGHIJKLMN/opciones"
```

**Response (200):**
```json
{
  "id": "01J9AGUA123ABCDEFGHIJKLMN",
  "nombre": "Agua Mineral",
  "descripcion": "Agua mineral natural 500ml",
  "precio_base": "3.00",
  "tipos_opciones": []
}
```

## CASOS DE USO

### 1. Formulario de Personalización

```javascript
// Frontend: Construir formulario dinámico
const opciones = await fetch(`/api/v1/productos/${productoId}/opciones`);

opciones.tipos_opciones.forEach(tipo => {
  const grupo = crearGrupoOpciones(tipo.nombre_tipo);
  
  if (tipo.obligatorio) {
    grupo.setAttribute('required', true);
  }
  
  if (tipo.multiple_seleccion) {
    // Usar checkboxes
    tipo.opciones.forEach(op => crearCheckbox(op));
  } else {
    // Usar radio buttons
    tipo.opciones.forEach(op => crearRadio(op));
  }
});
```

### 2. Cálculo de Precio Total

```javascript
// Calcular precio con opciones seleccionadas
function calcularPrecioConOpciones(producto, opcionesSeleccionadas) {
  let precioTotal = parseFloat(producto.precio_base);
  
  opcionesSeleccionadas.forEach(opcionId => {
    // Buscar precio adicional en todas las opciones
    producto.tipos_opciones.forEach(tipo => {
      const opcion = tipo.opciones.find(op => op.id === opcionId);
      if (opcion) {
        precioTotal += parseFloat(opcion.precio_adicional);
      }
    });
  });
  
  return precioTotal.toFixed(2);
}
```

### 3. Validación de Selección

```javascript
// Validar que se cumplan las reglas de selección
function validarSeleccion(producto, seleccionadas) {
  const errores = [];
  
  producto.tipos_opciones.forEach(tipo => {
    const seleccionadasDelTipo = seleccionadas.filter(id => 
      tipo.opciones.some(op => op.id === id)
    );
    
    // Validar opciones obligatorias
    if (tipo.obligatorio && seleccionadasDelTipo.length === 0) {
      errores.push(`Debe seleccionar una opción de "${tipo.nombre_tipo}"`);
    }
    
    // Validar selección múltiple
    if (!tipo.multiple_seleccion && seleccionadasDelTipo.length > 1) {
      errores.push(`Solo puede seleccionar una opción de "${tipo.nombre_tipo}"`);
    }
  });
  
  return errores;
}
```

## INTEGRACIÓN CON PEDIDOS

### Flujo Completo: De Opciones a Pedido

```bash
# 1. Obtener opciones del producto
GET /api/v1/productos/01J9CEVI123.../opciones

# 2. Cliente selecciona opciones en el frontend
# - Ají picante (id: 01J9OPC789..., precio: +1.00)
# - Con choclo (id: 01J9OPC012..., precio: +3.00)

# 3. Crear pedido con opciones seleccionadas
POST /api/v1/pedidos/completo
{
  "items": [{
    "id_producto": "01J9CEVI123ABCDEFGHIJKLMN",
    "cantidad": 1,
    "precio_unitario": 30.00,
    "opciones": [
      {
        "id_producto_opcion": "01J9OPC789ABCDEFGHIJKLMN",
        "precio_adicional": 1.00
      },
      {
        "id_producto_opcion": "01J9OPC012ABCDEFGHIJKLMN", 
        "precio_adicional": 3.00
      }
    ]
  }]
}
```

## URLs COMPLETAS

### Producción
```
GET https://back-dp2.onrender.com/api/v1/productos/{producto_id}/opciones
```

### Local
```
GET http://127.0.0.1:8000/api/v1/productos/{producto_id}/opciones
```

## NOTAS TÉCNICAS

- 🎯 **Optimizado:** Agrupado por tipos para mejor UX
- 📱 **Responsive:** Estructura ideal para formularios móviles  
- 💰 **Precios:** Incluye precios adicionales para cálculo inmediato
- ✅ **Validación:** Metadata para validación del lado cliente
- 🔄 **Orden:** Campo `orden` para presentación consistente
