# Especificación (breve) — PUT Actualización Completa de Producto

[⬅ Volver al Módulo](../README.md) · [⬅ Índice](../../../README.md)

## META

- **Host (variable):**
  - **Prod:** `https://back-dp2.onrender.com`
  - **Local:** `http://127.0.0.1:8000`
- **Base Path (constante):** `/api/v1`
- **Recurso (constante):** `/productos/{producto_id}/completo`
- **HTTP Method:** `PUT`
- **Autenticación:** (Ninguna)
- **Notas:** Requiere enviar JSON completo en el body con todos los datos del producto.

**URL patrón (componentes separadas):**

```
{HOST}{BASE_PATH}/productos/{producto_id}/completo
```

## DESCRIPCIÓN

Actualiza **completamente** un producto con todos sus datos relacionados en una sola operación, incluyendo:
- Datos básicos del producto (nombre, descripción, precio, imagen, categoría, disponibilidad)
- Alérgenos asociados
- Secciones del menú donde aparece
- Tipos de opciones y opciones del producto

**Caso de uso típico:**
- Actualización masiva de productos desde un panel de administración
- Sincronización de datos de productos desde sistemas externos
- Modificación completa de la configuración de un producto

**Ventajas:**
- **Operación atómica:** Todo se actualiza en una sola transacción
- **Simplicidad:** Un solo endpoint para actualizar múltiples relaciones
- **Consistencia:** Garantiza que todos los datos se actualizan correctamente

## ENTRADA

### Path Params

**DICTIONARY**

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `producto_id` | string | YES | ULID | Identificador único del producto a actualizar. |

### Headers

**DICTIONARY**

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `Content-Type` | string | YES | `application/json` | Tipo de contenido del body. |
| `accept` | string | YES | `application/json` | Tipo de respuesta esperada. |

### BODY (Completo)

```json
{
  "nombre": "Pizza Margherita Premium",
  "descripcion": "Pizza artesanal con ingredientes frescos de la casa",
  "precio_base": "18.50",
  "imagen_path": "/static/productos/pizza-margherita-premium.jpg",
  "imagen_alt_text": "Pizza Margherita con tomate fresco y mozzarella",
  "id_categoria": "01K7ZCT9QRST3K9FC94OIB2NL5",
  "disponible": true,
  "destacado": true,
  "alergenos": [
    "01K7ZCT8PNJA2J8EB83NHA1MK4",
    "01K7ZCT8PNJA2J8EB83NHA1MK5"
  ],
  "secciones": [
    {
      "id_seccion": "01K7ZCT9QRST3K9FC94OIB2NL6"
    },
    {
      "id_seccion": "01K7ZCT9QRST3K9FC94OIB2NL7"
    }
  ],
  "tipos_opciones": [
    {
      "id_tipo_opcion": "01K7ZCT9QRST3K9FC94OIB2NL8",
      "nombre": "Tamaño",
      "descripcion": "Seleccione el tamaño de su pizza",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden": 0,
      "opciones": [
        {
          "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NL9",
          "nombre": "Pequeña",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0
        },
        {
          "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NM0",
          "nombre": "Mediana",
          "precio_adicional": "3.00",
          "activo": true,
          "orden": 1
        },
        {
          "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NM1",
          "nombre": "Grande",
          "precio_adicional": "6.00",
          "activo": true,
          "orden": 2
        }
      ]
    },
    {
      "id_tipo_opcion": "01K7ZCT9QRST3K9FC94OIB2NM2",
      "nombre": "Ingredientes Extra",
      "descripcion": "Añade ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": 5,
      "orden": 1,
      "opciones": [
        {
          "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NM3",
          "nombre": "Champiñones",
          "precio_adicional": "2.00",
          "activo": true,
          "orden": 0
        },
        {
          "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NM4",
          "nombre": "Aceitunas",
          "precio_adicional": "1.50",
          "activo": true,
          "orden": 1
        }
      ]
    }
  ]
}
```

### DICTIONARY (BODY - Datos Básicos)

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `nombre` | string | YES | 3-200 caracteres | Nombre del producto (único por categoría). |
| `descripcion` | string | NO | | Descripción detallada del producto. |
| `precio_base` | string | YES | Decimal (2 decimales) | Precio base sin opciones adicionales. |
| `imagen_path` | string | NO | URL o path | Ruta de la imagen del producto. |
| `imagen_alt_text` | string | NO | | Texto alternativo para accesibilidad. |
| `id_categoria` | string | YES | ULID | ID de la categoría del producto. |
| `disponible` | boolean | YES | | Indica si el producto está disponible. |
| `destacado` | boolean | NO | | Indica si el producto aparece destacado. |

### DICTIONARY (BODY - Relaciones)

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `alergenos` | array[string] | NO | Array de ULIDs | Lista de IDs de alérgenos del producto. |
| `secciones` | array[object] | NO | Array de objetos | Secciones del menú donde aparece. |
| `secciones[].id_seccion` | string | YES | ULID | ID de la sección. |
| `tipos_opciones` | array[object] | NO | Array de objetos | Tipos de opciones y sus opciones. |

### DICTIONARY (BODY - Tipos de Opciones)

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `tipos_opciones[].id_tipo_opcion` | string | NO | ULID | ID del tipo de opción (si existe). |
| `tipos_opciones[].nombre` | string | YES | | Nombre del tipo (ej: "Tamaño"). |
| `tipos_opciones[].descripcion` | string | NO | | Descripción del tipo de opción. |
| `tipos_opciones[].seleccion_minima` | integer | YES | >= 0 | Mínimo de opciones a seleccionar. |
| `tipos_opciones[].seleccion_maxima` | integer | YES | >= 0 | Máximo de opciones a seleccionar. |
| `tipos_opciones[].orden` | integer | YES | >= 0 | Orden de visualización. |
| `tipos_opciones[].opciones` | array[object] | YES | | Opciones disponibles. |

### DICTIONARY (BODY - Opciones)

| Field | Data Type | Required | Format | Comment |
|-------|-----------|----------|--------|---------|
| `opciones[].id_opcion` | string | NO | ULID | ID de la opción (si existe). |
| `opciones[].nombre` | string | YES | | Nombre de la opción (ej: "Grande"). |
| `opciones[].precio_adicional` | string | YES | Decimal (2 decimales) | Precio extra de esta opción. |
| `opciones[].activo` | boolean | YES | | Si la opción está activa. |
| `opciones[].orden` | integer | YES | >= 0 | Orden de visualización. |

## SALIDA (200 OK — ejemplo)

```json
{
  "id": "01K7ZD12XYZW4M5NG95PJC3NO6",
  "nombre": "Pizza Margherita Premium",
  "descripcion": "Pizza artesanal con ingredientes frescos de la casa",
  "precio_base": "18.50",
  "imagen_path": "/static/productos/pizza-margherita-premium.jpg",
  "imagen_alt_text": "Pizza Margherita con tomate fresco y mozzarella",
  "id_categoria": "01K7ZCT9QRST3K9FC94OIB2NL5",
  "disponible": true,
  "destacado": true,
  "alergenos": [
    {
      "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
      "nombre": "Gluten",
      "icono": "gluten.png",
      "nivel_riesgo": "alto"
    },
    {
      "id": "01K7ZCT8PNJA2J8EB83NHA1MK5",
      "nombre": "Lactosa",
      "icono": "lactosa.png",
      "nivel_riesgo": "medio"
    }
  ],
  "fecha_creacion": "2024-10-23T05:16:30.123456Z",
  "fecha_modificacion": "2024-10-23T08:45:12.789012Z",
  "tipos_opciones": [
    {
      "id_tipo_opcion": "01K7ZCT9QRST3K9FC94OIB2NL8",
      "nombre_tipo": "Tamaño",
      "descripcion_tipo": "Seleccione el tamaño de su pizza",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden_tipo": 0,
      "opciones": [
        {
          "id": "01K7ZCT9QRST3K9FC94OIB2NL9",
          "nombre": "Pequeña",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0,
          "fecha_creacion": "2024-10-23T05:16:30.123456Z",
          "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
        },
        {
          "id": "01K7ZCT9QRST3K9FC94OIB2NM0",
          "nombre": "Mediana",
          "precio_adicional": "3.00",
          "activo": true,
          "orden": 1,
          "fecha_creacion": "2024-10-23T05:16:30.123456Z",
          "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
        },
        {
          "id": "01K7ZCT9QRST3K9FC94OIB2NM1",
          "nombre": "Grande",
          "precio_adicional": "6.00",
          "activo": true,
          "orden": 2,
          "fecha_creacion": "2024-10-23T05:16:30.123456Z",
          "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
        }
      ]
    },
    {
      "id_tipo_opcion": "01K7ZCT9QRST3K9FC94OIB2NM2",
      "nombre_tipo": "Ingredientes Extra",
      "descripcion_tipo": "Añade ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": 5,
      "orden_tipo": 1,
      "opciones": [
        {
          "id": "01K7ZCT9QRST3K9FC94OIB2NM3",
          "nombre": "Champiñones",
          "precio_adicional": "2.00",
          "activo": true,
          "orden": 0,
          "fecha_creacion": "2024-10-23T05:16:30.123456Z",
          "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
        },
        {
          "id": "01K7ZCT9QRST3K9FC94OIB2NM4",
          "nombre": "Aceitunas",
          "precio_adicional": "1.50",
          "activo": true,
          "orden": 1,
          "fecha_creacion": "2024-10-23T05:16:30.123456Z",
          "fecha_modificacion": "2024-10-23T05:16:30.123456Z"
        }
      ]
    }
  ]
}
```

## ERRORES (4xx/5xx)

### Error 400 - Datos de validación inválidos

```json
{
  "detail": "Los datos de entrada son inválidos"
}
```

### Error 404 - Producto no encontrado

```json
{
  "detail": "No se encontró el producto con ID '01K7ZD12XYZW4M5NG95PJC3NO6'"
}
```

### Error 409 - Conflicto (nombre duplicado)

```json
{
  "detail": "Ya existe un producto con el nombre 'Pizza Margherita Premium'"
}
```

### Error 500 - Error interno del servidor

```json
{
  "detail": "Error interno del servidor: Database transaction failed"
}
```

**Tabla de errores:**

| HTTP | Code | Title / Message | Comment |
|------|------|-----------------|---------|
| 400 | `VALIDATION_ERROR` | Datos inválidos | Precio negativo, campos vacíos, formato incorrecto. |
| 404 | `NOT_FOUND` | Producto no encontrado | El ID de producto no existe en la base de datos. |
| 409 | `CONFLICT` | Nombre duplicado | Ya existe un producto con ese nombre en la categoría. |
| 422 | `UNPROCESSABLE_ENTITY` | Error de validación Pydantic | Schema JSON inválido. |
| 500 | `INTERNAL_ERROR` | Error interno | Error inesperado del servidor. Revisar logs. |

## URLs completas (listas para usar)

### **Producción**

**URL completa:** `https://back-dp2.onrender.com/api/v1/productos/01K7ZD12XYZW4M5NG95PJC3NO6/completo`

**cURL (ejemplo completo):**

```bash
curl -X PUT \
  "https://back-dp2.onrender.com/api/v1/productos/01K7ZD12XYZW4M5NG95PJC3NO6/completo" \
  -H "Content-Type: application/json" \
  -H "accept: application/json" \
  -d '{
    "nombre": "Pizza Margherita Premium",
    "descripcion": "Pizza artesanal con ingredientes frescos de la casa",
    "precio_base": "18.50",
    "imagen_path": "/static/productos/pizza-margherita-premium.jpg",
    "imagen_alt_text": "Pizza Margherita con tomate fresco y mozzarella",
    "id_categoria": "01K7ZCT9QRST3K9FC94OIB2NL5",
    "disponible": true,
    "destacado": true,
    "alergenos": [
      "01K7ZCT8PNJA2J8EB83NHA1MK4",
      "01K7ZCT8PNJA2J8EB83NHA1MK5"
    ],
    "secciones": [],
    "tipos_opciones": [
      {
        "id_tipo_opcion": "01K7ZCT9QRST3K9FC94OIB2NL8",
        "nombre": "Tamaño",
        "descripcion": "Seleccione el tamaño de su pizza",
        "seleccion_minima": 1,
        "seleccion_maxima": 1,
        "orden": 0,
        "opciones": [
          {
            "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NL9",
            "nombre": "Pequeña",
            "precio_adicional": "0.00",
            "activo": true,
            "orden": 0
          },
          {
            "id_opcion": "01K7ZCT9QRST3K9FC94OIB2NM1",
            "nombre": "Grande",
            "precio_adicional": "6.00",
            "activo": true,
            "orden": 1
          }
        ]
      }
    ]
  }'
```

**JavaScript (fetch):**

```javascript
const productoId = '01K7ZD12XYZW4M5NG95PJC3NO6';
const productoData = {
  nombre: "Pizza Margherita Premium",
  descripcion: "Pizza artesanal con ingredientes frescos de la casa",
  precio_base: "18.50",
  imagen_path: "/static/productos/pizza-margherita-premium.jpg",
  imagen_alt_text: "Pizza Margherita con tomate fresco y mozzarella",
  id_categoria: "01K7ZCT9QRST3K9FC94OIB2NL5",
  disponible: true,
  destacado: true,
  alergenos: [
    "01K7ZCT8PNJA2J8EB83NHA1MK4",
    "01K7ZCT8PNJA2J8EB83NHA1MK5"
  ],
  secciones: [],
  tipos_opciones: [
    {
      id_tipo_opcion: "01K7ZCT9QRST3K9FC94OIB2NL8",
      nombre: "Tamaño",
      descripcion: "Seleccione el tamaño de su pizza",
      seleccion_minima: 1,
      seleccion_maxima: 1,
      orden: 0,
      opciones: [
        {
          id_opcion: "01K7ZCT9QRST3K9FC94OIB2NL9",
          nombre: "Pequeña",
          precio_adicional: "0.00",
          activo: true,
          orden: 0
        },
        {
          id_opcion: "01K7ZCT9QRST3K9FC94OIB2NM1",
          nombre: "Grande",
          precio_adicional: "6.00",
          activo: true,
          orden: 1
        }
      ]
    }
  ]
};

const response = await fetch(
  `https://back-dp2.onrender.com/api/v1/productos/${productoId}/completo`,
  {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'accept': 'application/json'
    },
    body: JSON.stringify(productoData)
  }
);

const data = await response.json();
console.log('Producto actualizado:', data);
```

### **Local**

**URL completa:** `http://127.0.0.1:8000/api/v1/productos/01K7ZD12XYZW4M5NG95PJC3NO6/completo`

**cURL:**

```bash
curl -X PUT \
  "http://127.0.0.1:8000/api/v1/productos/01K7ZD12XYZW4M5NG95PJC3NO6/completo" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Pizza Test", "precio_base": "15.00", "id_categoria": "01K7ZCT9QRST3K9FC94OIB2NL5", "disponible": true, "destacado": false, "alergenos": [], "secciones": [], "tipos_opciones": []}'
```

## EJEMPLO COMPLETO DE USO

### Escenario: Panel de administración que actualiza producto completo

```javascript
async function actualizarProductoCompleto(productoId, datosProducto) {
  try {
    // Preparar los datos del producto
    const productoCompleto = {
      // Datos básicos
      nombre: datosProducto.nombre,
      descripcion: datosProducto.descripcion,
      precio_base: datosProducto.precioBase.toFixed(2),
      imagen_path: datosProducto.imagenPath,
      imagen_alt_text: datosProducto.imagenAlt,
      id_categoria: datosProducto.idCategoria,
      disponible: datosProducto.disponible,
      destacado: datosProducto.destacado,
      
      // Alérgenos (array de IDs)
      alergenos: datosProducto.alergenosSeleccionados,
      
      // Secciones
      secciones: datosProducto.seccionesSeleccionadas.map(id => ({
        id_seccion: id
      })),
      
      // Tipos de opciones con sus opciones
      tipos_opciones: datosProducto.tiposOpciones.map((tipo, tipoIndex) => ({
        id_tipo_opcion: tipo.id || undefined,
        nombre: tipo.nombre,
        descripcion: tipo.descripcion,
        seleccion_minima: tipo.seleccionMinima,
        seleccion_maxima: tipo.seleccionMaxima,
        orden: tipoIndex,
        opciones: tipo.opciones.map((opcion, opcionIndex) => ({
          id_opcion: opcion.id || undefined,
          nombre: opcion.nombre,
          precio_adicional: opcion.precioAdicional.toFixed(2),
          activo: opcion.activo,
          orden: opcionIndex
        }))
      }))
    };

    // Realizar la petición PUT
    const response = await fetch(
      `https://back-dp2.onrender.com/api/v1/productos/${productoId}/completo`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify(productoCompleto)
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al actualizar producto');
    }

    const productoActualizado = await response.json();
    console.log('✅ Producto actualizado exitosamente:', productoActualizado);
    return productoActualizado;

  } catch (error) {
    console.error('❌ Error al actualizar producto:', error);
    throw error;
  }
}

// Ejemplo de uso
const datosEjemplo = {
  nombre: "Pizza Margherita Premium",
  descripcion: "Pizza artesanal con ingredientes frescos",
  precioBase: 18.50,
  imagenPath: "/static/productos/pizza-margherita-premium.jpg",
  imagenAlt: "Pizza Margherita Premium",
  idCategoria: "01K7ZCT9QRST3K9FC94OIB2NL5",
  disponible: true,
  destacado: true,
  alergenosSeleccionados: [
    "01K7ZCT8PNJA2J8EB83NHA1MK4", // Gluten
    "01K7ZCT8PNJA2J8EB83NHA1MK5"  // Lactosa
  ],
  seccionesSeleccionadas: [],
  tiposOpciones: [
    {
      id: "01K7ZCT9QRST3K9FC94OIB2NL8",
      nombre: "Tamaño",
      descripcion: "Seleccione el tamaño de su pizza",
      seleccionMinima: 1,
      seleccionMaxima: 1,
      opciones: [
        {
          id: "01K7ZCT9QRST3K9FC94OIB2NL9",
          nombre: "Pequeña",
          precioAdicional: 0.00,
          activo: true
        },
        {
          id: "01K7ZCT9QRST3K9FC94OIB2NM1",
          nombre: "Grande",
          precioAdicional: 6.00,
          activo: true
        }
      ]
    }
  ]
};

actualizarProductoCompleto('01K7ZD12XYZW4M5NG95PJC3NO6', datosEjemplo)
  .then(producto => {
    console.log('Producto guardado:', producto.nombre);
  })
  .catch(error => {
    console.error('Falló la actualización:', error.message);
  });
```

## Variables y constantes (resumen)

**Constantes:**
- `BASE_PATH = /api/v1`
- `RECURSO = /productos/{producto_id}/completo`

**Variables:**
- `HOST` = `https://back-dp2.onrender.com` (prod) | `http://127.0.0.1:8000` (local)
- `producto_id` — ID del producto a actualizar

## REGLAS DE NEGOCIO

- ✅ **Operación atómica:** Todos los cambios se aplican en una sola transacción
- ✅ **Validación completa:** Se validan todos los datos antes de actualizar
- ✅ **Nombre único:** El nombre debe ser único dentro de la categoría
- ✅ **Precios válidos:** El precio base y precios adicionales deben ser >= 0
- ✅ **Relaciones válidas:** Se verifica que los IDs de categoría, alérgenos y secciones existan
- ✅ **Estructura opciones:** Cada tipo de opción debe tener al menos una opción
- ⚠️ **Actualización parcial de relaciones:** Los TODO en el código indican que alérgenos, secciones y tipos de opciones aún no se actualizan completamente (solo datos básicos)

## NOTAS TÉCNICAS

- **Transacción:** La operación completa se ejecuta en una transacción de base de datos
- **Performance:** Considerar el tamaño del JSON si hay muchas opciones
- **Alternativa:** Para actualizar solo datos básicos, usar `PUT /productos/{producto_id}`
- **Implementación actual:** Los datos básicos del producto se actualizan correctamente. La actualización de relaciones (alérgenos, secciones, opciones) está marcada como TODO en el código
- **Validación Pydantic:** El schema valida estrictamente la estructura JSON (`extra='forbid'`)

## LIMITACIONES ACTUALES

⚠️ **IMPORTANTE:** Actualmente, este endpoint actualiza **solo los datos básicos** del producto. Las siguientes funcionalidades están pendientes de implementación:

- ❌ Actualización de alérgenos asociados
- ❌ Actualización de secciones del menú
- ❌ Actualización de tipos de opciones y opciones

**Para implementar completamente**, se deben descomentar y desarrollar los métodos:
- `_update_producto_alergenos(producto_id, alergenos_ids)`
- `_update_producto_secciones(producto_id, secciones)`
- `_update_producto_tipos_opciones(producto_id, tipos_opciones)`

Estos están marcados como `# TODO:` en `src/business_logic/menu/producto_service.py` líneas 651-658.
