# Contratos de API - Gestión de Productos

Este documento describe los contratos de las APIs para la actualización completa de productos y la gestión de imágenes.

---

## 1. API: Actualizar Producto Completo

### Endpoint
```
PUT /api/v1/productos/{producto_id}/completo
```

### Descripción
Actualiza completamente un producto con todos sus datos relacionados en una sola operación:
- Datos básicos del producto (nombre, descripción, precio, etc.)
- Lista de alérgenos asociados
- Secciones del producto
- Tipos de opciones con sus opciones correspondientes

### Parámetros de URL

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | string (ULID) | Sí | ID único del producto a actualizar |

### Headers Requeridos
```http
Content-Type: application/json
```

### Request Body

```typescript
{
  // Datos básicos del producto
  nombre: string;                    // REQUERIDO. Nombre del producto
  descripcion: string | null;        // OPCIONAL. Descripción detallada
  precio_base: string | number;      // REQUERIDO. Precio base (se convierte a Decimal)
  imagen_path: string | null;        // OPCIONAL. Ruta de la imagen (/static/images/productos/...)
  imagen_alt_text: string | null;    // OPCIONAL. Texto alternativo para la imagen
  id_categoria: string;               // REQUERIDO. ULID de la categoría
  disponible: boolean;                // REQUERIDO. Si el producto está disponible
  destacado: boolean;                 // REQUERIDO. Si el producto está destacado

  // Alérgenos del producto
  alergenos: Array<{
    id_alergeno: string;              // REQUERIDO. ULID del alérgeno
    nivel_presencia: "contiene" | "trazas" | "puede_contener";  // REQUERIDO
    notas: string | null;             // OPCIONAL. Notas adicionales (max 255 caracteres)
  }>;

  // Secciones del producto
  secciones: Array<{
    id_seccion: string;               // REQUERIDO. ULID de la sección
  }>;

  // Tipos de opciones con sus opciones
  tipos_opciones: Array<{
    id_tipo_opcion: string;           // REQUERIDO. ULID del tipo de opción (ej: "Tamaño", "Nivel de Ají")
    nombre: string;                   // REQUERIDO. Nombre del tipo de opción
    descripcion: string | null;       // OPCIONAL. Descripción del tipo
    seleccion_minima: number;         // REQUERIDO. Mínimo de opciones a seleccionar
    seleccion_maxima: number;         // REQUERIDO. Máximo de opciones a seleccionar
    orden: number;                    // REQUERIDO. Orden de visualización

    opciones: Array<{
      id_opcion: string | null;       // OPCIONAL. Si es null, crea nueva opción. Si tiene valor, actualiza existente
      nombre: string;                 // REQUERIDO. Nombre de la opción (ej: "Pequeño", "Mediano")
      precio_adicional: string | number;  // REQUERIDO. Precio adicional (puede ser 0)
      activo: boolean;                // REQUERIDO. Si la opción está activa
      orden: number;                  // REQUERIDO. Orden de visualización
    }>;
  }>;
}
```

### Ejemplo de Request - Producto Completo

```json
{
  "nombre": "Pizza Margherita Completa",
  "descripcion": "Pizza clásica italiana con ingredientes frescos",
  "precio_base": "15.50",
  "imagen_path": "/static/images/productos/pizza-margherita.jpg",
  "imagen_alt_text": "Pizza Margherita con tomate y mozzarella",
  "id_categoria": "01KA9TRZE8ABCDEFGHIJKLMNOP",
  "disponible": true,
  "destacado": false,

  "alergenos": [
    {
      "id_alergeno": "01KA9TRZE8GLUTEN123456789",
      "nivel_presencia": "contiene",
      "notas": "Contiene gluten de trigo"
    },
    {
      "id_alergeno": "01KA9TRZE8LACTEOS12345678",
      "nivel_presencia": "contiene",
      "notas": "Contiene lácteos (mozzarella)"
    }
  ],

  "secciones": [
    {"id_seccion": "01KA9TRZE8SECCION1234567"},
    {"id_seccion": "01KA9TRZE8SECCION7654321"}
  ],

  "tipos_opciones": [
    {
      "id_tipo_opcion": "01KA9TRZE8TAMANO123456789",
      "nombre": "Tamaño",
      "descripcion": "Seleccione el tamaño de la pizza",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden": 0,
      "opciones": [
        {
          "id_opcion": null,
          "nombre": "Personal (8 pulgadas)",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0
        },
        {
          "id_opcion": null,
          "nombre": "Mediana (12 pulgadas)",
          "precio_adicional": "5.00",
          "activo": true,
          "orden": 1
        },
        {
          "id_opcion": null,
          "nombre": "Familiar (16 pulgadas)",
          "precio_adicional": "10.00",
          "activo": true,
          "orden": 2
        }
      ]
    },
    {
      "id_tipo_opcion": "01KA9TRZE8EXTRAS1234567890",
      "nombre": "Ingredientes Extra",
      "descripcion": "Agregue ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": 5,
      "orden": 1,
      "opciones": [
        {
          "id_opcion": null,
          "nombre": "Champiñones",
          "precio_adicional": "2.50",
          "activo": true,
          "orden": 0
        },
        {
          "id_opcion": null,
          "nombre": "Aceitunas",
          "precio_adicional": "2.00",
          "activo": true,
          "orden": 1
        }
      ]
    }
  ]
}
```

### Ejemplo de Request - Producto Simple (sin alérgenos ni opciones)

```json
{
  "nombre": "Ensalada César",
  "descripcion": "Ensalada fresca con aderezo César",
  "precio_base": "12.00",
  "imagen_path": "/static/images/productos/ensalada-cesar.jpg",
  "imagen_alt_text": "Ensalada César fresca",
  "id_categoria": "01KA9TRZE8CATEGORIA123456",
  "disponible": true,
  "destacado": true,
  "alergenos": [],
  "secciones": [],
  "tipos_opciones": []
}
```

### Response Body (200 OK)

```typescript
{
  // Datos básicos del producto
  id: string;                         // ULID del producto
  nombre: string;
  descripcion: string | null;
  precio_base: string;                // Decimal como string (ej: "15.50")
  imagen_path: string | null;
  imagen_alt_text: string | null;
  id_categoria: string;
  disponible: boolean;
  destacado: boolean;
  fecha_creacion: string;             // ISO 8601 datetime
  fecha_actualizacion: string;        // ISO 8601 datetime

  // Tipos de opciones agrupados
  tipos_opciones: Array<{
    id_tipo_opcion: string;
    nombre_tipo: string;
    descripcion_tipo: string | null;
    seleccion_minima: number;
    seleccion_maxima: number;
    orden_tipo: number;

    opciones: Array<{
      id: string;                     // ULID de la opción (generado automáticamente)
      nombre: string;
      precio_adicional: string;       // Decimal como string
      activo: boolean;
      orden: number;
    }>;
  }>;
}
```

### Ejemplo de Response (200 OK)

```json
{
  "id": "01KA9TRZE8PRODUCTO123456789",
  "nombre": "Pizza Margherita Completa",
  "descripcion": "Pizza clásica italiana con ingredientes frescos",
  "precio_base": "15.50",
  "imagen_path": "/static/images/productos/pizza-margherita.jpg",
  "imagen_alt_text": "Pizza Margherita con tomate y mozzarella",
  "id_categoria": "01KA9TRZE8ABCDEFGHIJKLMNOP",
  "disponible": true,
  "destacado": false,
  "fecha_creacion": "2024-01-15T10:30:00",
  "fecha_actualizacion": "2024-01-15T14:45:00",

  "tipos_opciones": [
    {
      "id_tipo_opcion": "01KA9TRZE8TAMANO123456789",
      "nombre_tipo": "Tamaño",
      "descripcion_tipo": "Seleccione el tamaño de la pizza",
      "seleccion_minima": 1,
      "seleccion_maxima": 1,
      "orden_tipo": 0,
      "opciones": [
        {
          "id": "01KAF7HZSYOPCION1234567890",
          "nombre": "Personal (8 pulgadas)",
          "precio_adicional": "0.00",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYOPCION0987654321",
          "nombre": "Mediana (12 pulgadas)",
          "precio_adicional": "5.00",
          "activo": true,
          "orden": 1
        },
        {
          "id": "01KAF7HZSYOPCION1122334455",
          "nombre": "Familiar (16 pulgadas)",
          "precio_adicional": "10.00",
          "activo": true,
          "orden": 2
        }
      ]
    },
    {
      "id_tipo_opcion": "01KA9TRZE8EXTRAS1234567890",
      "nombre_tipo": "Ingredientes Extra",
      "descripcion_tipo": "Agregue ingredientes adicionales",
      "seleccion_minima": 0,
      "seleccion_maxima": 5,
      "orden_tipo": 1,
      "opciones": [
        {
          "id": "01KAF7HZSYOPCION5544332211",
          "nombre": "Champiñones",
          "precio_adicional": "2.50",
          "activo": true,
          "orden": 0
        },
        {
          "id": "01KAF7HZSYOPCION6655443322",
          "nombre": "Aceitunas",
          "precio_adicional": "2.00",
          "activo": true,
          "orden": 1
        }
      ]
    }
  ]
}
```

### Códigos de Estado HTTP

| Código | Descripción | Ejemplo de Error |
|--------|-------------|------------------|
| `200 OK` | Producto actualizado exitosamente | - |
| `400 Bad Request` | Datos de entrada inválidos | Campos requeridos faltantes, formato incorrecto |
| `404 Not Found` | Producto no encontrado | El `producto_id` no existe |
| `409 Conflict` | Conflicto con datos existentes | Nombre de producto duplicado |
| `422 Unprocessable Entity` | Error de validación de Pydantic | Tipo de dato incorrecto, valores fuera de rango |
| `500 Internal Server Error` | Error interno del servidor | Error de base de datos, error no manejado |

### Ejemplo de Error (400 Bad Request)

```json
{
  "detail": "El campo 'nombre' es requerido"
}
```

### Ejemplo de Error (404 Not Found)

```json
{
  "detail": "Producto con ID '01KA9TRZE8INVALID123456' no encontrado"
}
```

### Ejemplo de Error (422 Unprocessable Entity)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "nombre"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

---

## Comportamiento Importante: Soft Delete de Opciones

### ⚠️ IMPORTANTE: Cómo Eliminar Opciones

Para **ELIMINAR** opciones de un producto, **NO** se debe enviar un array vacío en `tipos_opciones`. En su lugar:

1. **Para eliminar TODAS las opciones de un tipo**: Enviar el tipo con `opciones: []`
   ```json
   {
     "tipos_opciones": [
       {
         "id_tipo_opcion": "01KA9TRZE8TAMANO123456789",
         "nombre": "Tamaño",
         "descripcion": "Seleccione el tamaño",
         "seleccion_minima": 1,
         "seleccion_maxima": 1,
         "orden": 0,
         "opciones": []  // ← Esto DESACTIVA todas las opciones de este tipo
       }
     ]
   }
   ```

2. **Para eliminar opciones específicas**: NO incluir esas opciones en el array (solo enviar las que quieres mantener)
   ```json
   {
     "tipos_opciones": [
       {
         "id_tipo_opcion": "01KA9TRZE8TAMANO123456789",
         "nombre": "Tamaño",
         "opciones": [
           {
             "id_opcion": "01KAF7HZSYOPCION1234567890",  // ← Solo esta opción se mantiene activa
             "nombre": "Personal",
             "precio_adicional": "0.00",
             "activo": true,
             "orden": 0
           }
           // Las demás opciones se DESACTIVAN automáticamente
         ]
       }
     ]
   }
   ```

3. **Para restaurar opciones previamente desactivadas**: Enviar el `id_opcion` con `activo: true`
   ```json
   {
     "opciones": [
       {
         "id_opcion": "01KAF7HZSYOPCION1234567890",  // ← ID de opción existente
         "nombre": "Personal",
         "precio_adicional": "0.00",
         "activo": true,  // ← Se REACTIVA
         "orden": 0
       }
     ]
   }
   ```

### Reglas de Gestión de Opciones

| Acción | Cómo Hacerlo |
|--------|--------------|
| **Crear nueva opción** | Enviar `id_opcion: null` |
| **Actualizar opción existente** | Enviar `id_opcion: "<ULID_existente>"` |
| **Desactivar opción** | NO incluir la opción en el array O enviar con `activo: false` |
| **Reactivar opción** | Enviar `id_opcion: "<ULID_existente>"` con `activo: true` |
| **Desactivar todas las opciones de un tipo** | Enviar el tipo con `opciones: []` |

---

## 2. API: Actualizar Imagen de Producto

### Endpoint
```
PUT /api/v1/productos/{producto_id}/imagen
```

### Descripción
Sube o actualiza la imagen de un producto. Si el producto ya tiene una imagen, la reemplaza automáticamente y elimina la imagen anterior del servidor.

### Parámetros de URL

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `producto_id` | string (ULID) | Sí | ID único del producto |

### Headers Requeridos
```http
Content-Type: multipart/form-data
```

### Request Body (Form Data)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `file` | File | Sí | Archivo de imagen a subir |

### Restricciones del Archivo

| Restricción | Valor |
|-------------|-------|
| **Extensiones permitidas** | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` |
| **Tamaño máximo** | 5 MB (5,242,880 bytes) |
| **Formatos soportados** | JPEG, PNG, WebP, GIF |

### Ejemplo de Request (JavaScript/Fetch)

```javascript
// Crear FormData con la imagen
const formData = new FormData();
formData.append('file', imageFile);  // imageFile es un objeto File

// Enviar request
const response = await fetch('/api/v1/productos/01KA9TRZE8PRODUCTO123/imagen', {
  method: 'PUT',
  body: formData,
  // NO establecer Content-Type manualmente, el navegador lo hace automáticamente
});

const result = await response.json();
```

### Ejemplo de Request (React con input file)

```jsx
function ProductImageUpload({ productoId }) {
  const handleImageUpload = async (event) => {
    const file = event.target.files[0];

    if (!file) return;

    // Validar tamaño (5 MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('La imagen es muy grande. Máximo 5 MB');
      return;
    }

    // Validar tipo
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      alert('Tipo de archivo no permitido. Use JPG, PNG, WebP o GIF');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`/api/v1/productos/${productoId}/imagen`, {
        method: 'PUT',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error al subir imagen');
      }

      const result = await response.json();
      console.log('Imagen actualizada:', result.imagen_path);

    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <input
      type="file"
      accept=".jpg,.jpeg,.png,.webp,.gif"
      onChange={handleImageUpload}
    />
  );
}
```

### Ejemplo de Request (cURL)

```bash
curl -X PUT \
  "http://localhost:8000/api/v1/productos/01KA9TRZE8PRODUCTO123/imagen" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/ruta/a/imagen.jpg"
```

### Response Body (200 OK)

```typescript
{
  imagen_path: string;    // Ruta completa de la nueva imagen
  mensaje: string;        // Mensaje de confirmación
}
```

### Ejemplo de Response (200 OK)

```json
{
  "imagen_path": "/static/images/productos/01KAF7HZSYZCAXKKGDX93SH6SA.jpg",
  "mensaje": "Imagen actualizada correctamente"
}
```

### Códigos de Estado HTTP

| Código | Descripción | Ejemplo de Error |
|--------|-------------|------------------|
| `200 OK` | Imagen actualizada exitosamente | - |
| `400 Bad Request` | Archivo inválido | Archivo muy grande, tipo no permitido, sin nombre |
| `404 Not Found` | Producto no encontrado | El `producto_id` no existe |
| `500 Internal Server Error` | Error interno del servidor | Error al guardar archivo, permisos insuficientes |

### Ejemplo de Error (400 Bad Request - Archivo muy grande)

```json
{
  "detail": "Archivo muy grande. Máximo: 5.0MB"
}
```

### Ejemplo de Error (400 Bad Request - Tipo no permitido)

```json
{
  "detail": "Tipo de archivo no permitido. Use: .jpg, .jpeg, .png, .webp, .gif"
}
```

### Ejemplo de Error (400 Bad Request - Sin nombre)

```json
{
  "detail": "El archivo no tiene un nombre válido"
}
```

### Ejemplo de Error (404 Not Found)

```json
{
  "detail": "Producto con ID '01KA9TRZE8INVALID123456' no encontrado"
}
```

---

## 3. API: Eliminar Imagen de Producto

### ⚠️ Nota Importante
Actualmente **NO existe** un endpoint dedicado para eliminar la imagen de un producto. Para eliminar la imagen, use el endpoint de actualización completa:

```json
PUT /api/v1/productos/{producto_id}/completo

{
  "nombre": "Nombre del producto",
  "descripcion": "...",
  "precio_base": "10.00",
  "imagen_path": null,  // ← Esto elimina la imagen
  "imagen_alt_text": null,
  "id_categoria": "...",
  "disponible": true,
  "destacado": false,
  "alergenos": [],
  "secciones": [],
  "tipos_opciones": []
}
```

---

## Flujos de Trabajo Comunes

### Flujo 1: Crear Producto Completo desde Cero

1. **Crear producto básico** (POST `/api/v1/productos`)
2. **Subir imagen** (PUT `/api/v1/productos/{id}/imagen`)
3. **Actualizar con alérgenos y opciones** (PUT `/api/v1/productos/{id}/completo`)

### Flujo 2: Actualizar Producto Existente

1. **Obtener datos actuales** (GET `/api/v1/productos/{id}/opciones`)
2. **Modificar datos necesarios** (en frontend)
3. **Enviar actualización completa** (PUT `/api/v1/productos/{id}/completo`)

### Flujo 3: Cambiar Solo la Imagen

1. **Subir nueva imagen** (PUT `/api/v1/productos/{id}/imagen`)
2. *Automáticamente reemplaza la imagen anterior*

### Flujo 4: Agregar Opciones a Producto Existente

```javascript
// 1. Obtener producto actual
const producto = await fetch(`/api/v1/productos/${id}/opciones`).then(r => r.json());

// 2. Agregar nuevas opciones
const updatedData = {
  ...producto,
  tipos_opciones: [
    ...producto.tipos_opciones,
    {
      id_tipo_opcion: "01KA9TRZE8NUEVOTIPO12345",
      nombre: "Nuevo Tipo",
      descripcion: "Descripción del nuevo tipo",
      seleccion_minima: 1,
      seleccion_maxima: 1,
      orden: producto.tipos_opciones.length,
      opciones: [
        {
          id_opcion: null,  // ← Crear nueva opción
          nombre: "Opción 1",
          precio_adicional: "5.00",
          activo: true,
          orden: 0
        }
      ]
    }
  ]
};

// 3. Enviar actualización
await fetch(`/api/v1/productos/${id}/completo`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updatedData)
});
```

### Flujo 5: Eliminar Opciones de Producto

```javascript
// 1. Obtener producto actual
const producto = await fetch(`/api/v1/productos/${id}/opciones`).then(r => r.json());

// 2. Filtrar opciones a mantener
const updatedData = {
  ...producto,
  tipos_opciones: producto.tipos_opciones.map(tipo => ({
    ...tipo,
    opciones: tipo.opciones.filter(opcion =>
      opcion.id !== "01KAF7HZSYOPCION_A_ELIMINAR"
    )
  }))
};

// 3. Enviar actualización (las opciones no incluidas se desactivan)
await fetch(`/api/v1/productos/${id}/completo`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updatedData)
});
```

---

## Notas Importantes para Frontend

### 1. Gestión de Alérgenos

- **Enviar array vacío** `[]` para productos sin alérgenos
- **Solo se guardan alérgenos activos** (no hay soft delete para alérgenos)
- Para eliminar un alérgeno: simplemente no incluirlo en el array

### 2. Gestión de Opciones (Soft Delete)

- Las opciones usan **soft delete** (campo `activo: true/false`)
- Las opciones NO incluidas en el request se **desactivan automáticamente**
- Para **reactivar** una opción: incluir su `id_opcion` con `activo: true`
- Para **crear** una opción nueva: enviar `id_opcion: null`

### 3. Gestión de Imágenes

- Al subir nueva imagen, **la anterior se elimina automáticamente**
- Guardar el `imagen_path` retornado en el estado del producto
- La ruta siempre empieza con `/static/images/productos/`
- Validar tamaño y tipo **antes** de enviar al servidor

### 4. Conversión de Decimales

- El backend acepta `precio_base` como **string** o **number**
- El backend retorna `precio_base` como **string** (ej: `"15.50"`)
- Usar `parseFloat()` en frontend si necesitas operaciones matemáticas

### 5. ULIDs

- Todos los IDs son **ULID** (26 caracteres alfanuméricos)
- Ejemplo: `01KA9TRZE8PRODUCTO123456789`
- **No confundir con UUID** (formato diferente)

### 6. Fechas

- Formato: **ISO 8601** (ej: `"2024-01-15T10:30:00"`)
- Usar `new Date(fecha)` para convertir en frontend

---

## Ejemplos de Integración Frontend

### React + TypeScript

```typescript
interface ProductoCompleto {
  nombre: string;
  descripcion: string | null;
  precio_base: string;
  imagen_path: string | null;
  imagen_alt_text: string | null;
  id_categoria: string;
  disponible: boolean;
  destacado: boolean;
  alergenos: Array<{
    id_alergeno: string;
    nivel_presencia: "contiene" | "trazas" | "puede_contener";
    notas: string | null;
  }>;
  secciones: Array<{ id_seccion: string }>;
  tipos_opciones: Array<{
    id_tipo_opcion: string;
    nombre: string;
    descripcion: string | null;
    seleccion_minima: number;
    seleccion_maxima: number;
    orden: number;
    opciones: Array<{
      id_opcion: string | null;
      nombre: string;
      precio_adicional: string;
      activo: boolean;
      orden: number;
    }>;
  }>;
}

async function updateProducto(id: string, data: ProductoCompleto) {
  const response = await fetch(`/api/v1/productos/${id}/completo`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
}

async function uploadImage(productoId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`/api/v1/productos/${productoId}/imagen`, {
    method: 'PUT',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
}
```

---

## Validaciones Recomendadas en Frontend

### Antes de enviar actualización completa:

```javascript
function validateProducto(data) {
  const errors = [];

  // Validar campos requeridos
  if (!data.nombre || data.nombre.trim() === '') {
    errors.push('El nombre es requerido');
  }

  if (!data.precio_base || parseFloat(data.precio_base) <= 0) {
    errors.push('El precio debe ser mayor a 0');
  }

  if (!data.id_categoria) {
    errors.push('La categoría es requerida');
  }

  // Validar alérgenos
  data.alergenos.forEach((alergeno, index) => {
    if (!alergeno.id_alergeno) {
      errors.push(`Alérgeno ${index + 1}: ID es requerido`);
    }
    if (!['contiene', 'trazas', 'puede_contener'].includes(alergeno.nivel_presencia)) {
      errors.push(`Alérgeno ${index + 1}: Nivel de presencia inválido`);
    }
  });

  // Validar opciones
  data.tipos_opciones.forEach((tipo, tipoIndex) => {
    if (tipo.seleccion_minima < 0) {
      errors.push(`Tipo ${tipo.nombre}: Selección mínima debe ser >= 0`);
    }
    if (tipo.seleccion_maxima < tipo.seleccion_minima) {
      errors.push(`Tipo ${tipo.nombre}: Selección máxima debe ser >= mínima`);
    }

    tipo.opciones.forEach((opcion, opcionIndex) => {
      if (!opcion.nombre || opcion.nombre.trim() === '') {
        errors.push(`Tipo ${tipo.nombre}, Opción ${opcionIndex + 1}: Nombre requerido`);
      }
      if (parseFloat(opcion.precio_adicional) < 0) {
        errors.push(`Tipo ${tipo.nombre}, Opción ${opcion.nombre}: Precio no puede ser negativo`);
      }
    });
  });

  return errors;
}
```

### Antes de subir imagen:

```javascript
function validateImage(file) {
  const errors = [];

  // Validar tamaño (5 MB)
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    errors.push(`Archivo muy grande (${(file.size / 1024 / 1024).toFixed(2)} MB). Máximo: 5 MB`);
  }

  // Validar tipo
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  if (!allowedTypes.includes(file.type)) {
    errors.push(`Tipo de archivo no permitido: ${file.type}`);
  }

  return errors;
}
```

---

## Troubleshooting

### Problema: Error 422 al actualizar producto

**Solución**: Verificar que todos los campos requeridos estén presentes y tengan el tipo correcto.

```javascript
// ❌ Incorrecto
{ precio_base: 15.50 }  // Puede causar problemas de precisión

// ✅ Correcto
{ precio_base: "15.50" }  // String es más seguro para decimales
```

### Problema: Opciones no se eliminan

**Solución**: Enviar el tipo de opción con `opciones: []` o no incluir las opciones a eliminar.

```javascript
// ❌ Incorrecto (no hace nada)
{ tipos_opciones: [] }

// ✅ Correcto (elimina todas las opciones del tipo "Tamaño")
{
  tipos_opciones: [
    {
      id_tipo_opcion: "01KA9TRZE8TAMANO123456789",
      nombre: "Tamaño",
      // ... otros campos
      opciones: []  // ← Esto desactiva todas
    }
  ]
}
```

### Problema: Error 400 al subir imagen

**Solución**: Verificar extensión, tamaño y que el archivo exista.

```javascript
// Validar antes de enviar
const file = event.target.files[0];
if (!file) {
  console.error('No se seleccionó archivo');
  return;
}

const errors = validateImage(file);
if (errors.length > 0) {
  console.error('Errores de validación:', errors);
  return;
}
```

---

## Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2025-01-19 | Versión inicial del contrato de API |

---

**Contacto de Soporte**: Para dudas o problemas, contactar al equipo de backend.
